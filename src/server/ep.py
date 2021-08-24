import importlib
import pathlib
import route


class Argument:
    def __init__(self,
                 name: str,
                 type: str,
                 arg_in: str,
                 required: bool = True,
                 description: str = None,
                 auto_cast: bool = True,
                 minimum: int = -1,
                 maximum: int = -1,
                 must_be: (tuple, list) = ()):
        if type not in ["str", "string", "bool", "boolean", "number", "int", "double", "decimal", "float", "other"]:
            raise ValueError("Argument type is must be valid type.")
        if arg_in not in ["path", "query", "body"]:
            raise ValueError("Argument location is mut be valid type.")
        self.name = name
        self.type = type
        self.arg_in = arg_in
        self.required = required,
        self.description = description,
        self.auto_cast = auto_cast,
        self.min = minimum
        self.max = maximum
        self.must_be = must_be

    def norm_type(self, val=None):
        if "str" in self.type:
            return "string" if val is None else str(val)
        elif "bool" in self.type:
            return "bool" if val is None else bool(val)
        elif self.type is "number" and "int" in self.type:
            return "integer" if val is None else int(val)
        else:
            return "number" if val is None else float(val)

    def validate(self, param_dict):
        # NOT_FOUND = -1, OK = 0, NOT_MATCH = 1, TYPE_ERR = 2, MINIMUM_ERR = 3, MAXIMUM_ERR = 4
        name = self.name
        typ = self.type
        cast = self.auto_cast
        must_be = self.must_be
        min = self.min
        max = self.max

        if name not in param_dict and self.required:
            return -1

        value = param_dict[name]

        if "str" in typ:
            if len(must_be) is not 0 and value not in must_be:
                return 1

            if min is not -1 and len(value) < min:
                return 3

            if max is not -1 and len(value) > max:
                return 4

            if cast:
                param_dict[name] = str(value)

        elif "bool" in typ:
            if value not in ("true", "false") + self.must_be:
                return 1

            if cast:
                param_dict[name] = bool(value)
        elif typ == "other":
            return "OK"
        else:
            try:
                if "int" in self.type or self.type == "number":
                    val = int(value)
                else:
                    val = float(value)
            except ValueError:
                return 2

            if len(must_be) is not 0 and val not in must_be:
                return 1

            if min is not -1 and val < min:
                return 3

            if max is not -1 and val > max:
                return 4

            if cast:
                param_dict[name] = val

        return 0


class EndPoint:
    def __init__(self,
                 method: str,
                 route_path: str,
                 rel_path: str,
                 handler,
                 auth_required: bool = True,
                 args: list = None):
        self.method = method
        self.route_path = route_path
        self.rel_path = rel_path
        self.handler = handler
        self.auth_required = auth_required
        self.args = () if args is None else args

    def handle(self, handler, params):
        if self.auth_required and handler.do_auth():
            return

        if not self.validate_arg(handler, params):
            return

        self.handler(handler, params)

    def validate_arg(self, handler, params):

        missing = []

        for arg in self.args:
            arg: Argument
            code = arg.validate(params)
            if code == -1:
                missing.append(arg.name)
            elif code == 1:
                if "bool" in arg.type:
                    route.quick_invalid(handler, arg.name, "[" + ", ".join(("true", "false") + arg.must_be) + "]")
                    return False
                else:
                    route.quick_invalid(handler, arg.name, "[" + ", " + arg.must_be + "]")
                    return False
            elif code == 2:
                route.quick_invalid(handler, arg.name, arg.norm_type())
                return False
            elif code == 3:
                if "str" in arg.name:
                    route.quick_invalid(handler, arg.name, f"at least {arg.min} character")
                    return False
                else:
                    route.quick_invalid(handler, arg.name, f"at least {arg.min}")
                    return False
            elif code == 4:
                if "str" in arg.name:
                    route.quick_invalid(handler, arg.name, f"less than {arg.max} character")
                    return False
                else:
                    route.quick_invalid(handler, arg.name, f"less than {arg.max}")
                    return False

        if len(missing) is not 0:
            route.write(handler, 400, route.error(route.Cause.MISSING_FIELD, route.Cause.MISSING_FIELD[2]
                                                  .replace("%0", str(len(missing)))
                                                  .replace("%1", ", ".join(missing))))
            return False
        return True


global loader


class EPManager:
    def __init__(self):
        self.endpoints = []
        self.index = {}
        self.index_array = []
        self.signals = []

    def load(self, root):
        for file in pathlib.Path(root).glob("**/*.py"):
            try:
                m = ".".join(file.parts)[4:-3]
                importlib.import_module(m)
            except Exception as e:
                pass
        self._make_cache()

    def _make_cache(self):
        for s in self.signals:
            method = s["method"]
            function = s["func"]
            path = s["path"]
            auth = s["require_auth"]
            args = s["args"]

            rt = path
            if rt.endswith(".py"):
                rt = rt[:-3]

            if rt.endswith("_") and not rt.endswith("__"):
                if rt == "_":
                    rt = "/"
                else:
                    rt = rt[:-1]

            if rt in self.index and method in self.index[rt]:
                return

            if method.upper() in ["GET", "HEAD", "TRACE", "OPTIONS"]:
                for arg in args:
                    if arg.arg_in == "body":
                        raise TypeError("This method does not get a request body.")

            if rt not in self.index:
                self.index[rt] = []
            self.index_array.append(method + " " + rt)
            self.index[rt].append(method)
            self.endpoints.append(EndPoint(method, rt, path, function, auth, args))

    def get_endpoint(self, method, path):
        if path in self.index and method in self.index[path]:
            return self.endpoints[self.index_array.index(method + " " + path)]
        if path.endswith("/"):
            if path[:-1] in self.index_array:
                return self.endpoints[self.index_array.index(method + " " + path[:-1])]

        parts = path.split("/")

        for a in parts:
            dxt = path.replace(a, "__", 1)
            if (method + dxt) in self.index_array:
                return self.endpoints[self.index_array.index(method + " " + dxt)]
            if dxt.endswith("/"):
                if (method + dxt[:-1]) in self.index_array:
                    return self.endpoints[self.index_array.index(method + " " + dxt[:-1])]

        return None
