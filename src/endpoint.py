import importlib
import os
import pathlib

from enum import Enum
from route import quick_invalid, write, error, Cause


class Method(Enum):
    GET = "GET"
    HEAD = "HEAD"
    TRACE = "TRACE"
    OPTIONS = "OPTIONS"
    CONNECT = "CONNECT"

    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"

    @staticmethod
    def values():
        return [e.value for e in Method]


class Document:
    def __init__(self,
                 title: str = None,  # title or summary required
                 summary: str = None,
                 # description: str = "Description",
                 # desc: str = "Description",
                 types: (list, str) = "application/octet-stream",
                 example: (dict, str, int, float, bool, any) = None,
                 security: dict = None,
                 more: dict = None,
                 responses: list = None,
                 tags: list = None,
                 format: str = None):
        if title is None and summary is None:
            raise ValueError("Title or Summary must not be None.")
        self.title = summary if title is None else title
        # self.description = desc if description is None else description
        self.types = [types] if type(types) == str else types
        self.example = example
        self.security = security
        self.more = {} if more is None else more
        self.responses = [] if responses is None else responses
        self.tags = [] if tags is None else tags
        self.format = format


def http(method, require_auth: bool = True, args: tuple = (), docs: Document = None):
    def _context(handler):
        path = os.path.relpath(handler.__globals__["__file__"], "src/server/handler_root")
        path = path.replace(os.sep, "/")
        pp = 0

        if type(args) == list:
            arg3 = list(args)
        elif type(args) != tuple:
            arg3 = (args,)
        else:
            arg3 = args

        for arg in arg3:
            if arg.arg_in == "path" and "__" not in path:
                raise ValueError("Some args have a path specified, but the path does not have __.")
            if arg.arg_in == "path":
                pp += 1

        loader.signals.append({
            "method": method,
            "func": handler,
            "path": path,
            "require_auth": require_auth,
            "args": arg3,
            "docs": docs
        })
        return handler

    return _context


class Documentable:
    def __init__(self, document: Document = None):
        self.docs = document


class Argument(Documentable):
    def __init__(self, name: str, type: str, arg_in: str, required: bool = True, auto_cast: bool = True,
                 minimum: int = -1, maximum: int = -1, must_be: (tuple, list) = (), doc: Document = None,
                 format: str = None):
        super().__init__(doc)
        if type not in ["str", "string", "bool", "boolean", "number", "int", "long",
                        "double", "decimal", "float", "other"]:
            raise ValueError("Argument type is must be valid type.")
        if arg_in not in ["path", "query", "body"]:
            raise ValueError("Argument location is mut be valid type.")
        self.name = name
        self.type = type
        self.arg_in = arg_in
        self.required = required
        self.auto_cast = auto_cast
        self.min = minimum
        self.max = maximum
        self.must_be = must_be
        self.document = doc
        self.format = format

    def norm_type(self, val=None):
        if "str" in self.type:
            return "string" if val is None else str(val)
        elif "bool" in self.type:
            return "bool" if val is None else bool(val)
        elif self.type is "number" or "int" in self.type:
            return "integer" if val is None else int(val)
        elif self.type is "long":
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


class EndPoint(Documentable):
    def __init__(self, method: str, route_path: str, rel_path: str, handler, auth_required: bool = True,
                 args: list = None, path_arg: bool = False, doc: Document = None):
        super().__init__(doc)
        self.method = method
        self.route_path = route_path
        self.rel_path = rel_path
        self.handler = handler
        self.auth_required = auth_required
        self.args = () if args is None else args
        self.path_arg = path_arg

    def handle(self, handler, params, queries, path_param):
        if self.auth_required and handler.do_auth():
            return

        if not self.validate_arg(handler, params, queries, path_param):
            return

        self.handler(handler, params)

    def validate_arg(self, handler, params, queries, path_param):

        missing = []

        for arg in self.args:
            arg: Argument
            if arg.arg_in == "query":
                code = arg.validate(queries)
            elif arg.arg_in == "body":
                code = arg.validate(params)
            elif arg.arg_in == "path":
                code = arg.validate(path_param)
            else:
                raise ValueError(f"Validate failed: N:{arg.name} - T:{arg.type} - I:{arg.arg_in}")

            if code == -1:
                missing.append(arg.name)
            elif code == 1:
                if "bool" in arg.type:
                    quick_invalid(handler, arg.name, "[" + ", ".join(("true", "false") + arg.must_be) + "]")
                    return False
                else:
                    quick_invalid(handler, arg.name, "[" + ", " + arg.must_be + "]")
                    return False
            elif code == 2:
                quick_invalid(handler, arg.name, arg.norm_type())
                return False
            elif code == 3:
                if "str" in arg.name:
                    quick_invalid(handler, arg.name, f"at least {arg.min} character")
                    return False
                else:
                    quick_invalid(handler, arg.name, f"at least {arg.min}")
                    return False
            elif code == 4:
                if "str" in arg.name:
                    quick_invalid(handler, arg.name, f"less than {arg.max} character")
                    return False
                else:
                    quick_invalid(handler, arg.name, f"less than {arg.max}")
                    return False

            if arg.arg_in == "query":
                val = arg.norm_type(queries[arg.name]) if arg.auto_cast else queries[arg.name]
                params[arg.name] = val
            elif arg.arg_in == "path":
                val = arg.norm_type(path_param[arg.name]) if arg.auto_cast else path_param[arg.name]
                params[arg.name] = val

        if len(missing) is not 0:
            write(handler, 400, error(Cause.MISSING_FIELD, Cause.MISSING_FIELD[2]
                                      .replace("%0", str(len(missing)))
                                      .replace("%1", ", ".join(missing))))
            return False
        return True


class Response:
    def __init__(self, code: int = 0,
                 about: str = "Example response",
                 example: (dict, str, int, float, bool, any) = None):
        self.code = code
        self.about = about
        self.example = example


global loader


class EPManager:
    def __init__(self):
        global loader
        self.signals = []
        self.index_tree = {}
        self.known_source = []
        loader = self

    def load(self, root):
        for file in pathlib.Path(root).glob("**/*.py"):
            self.load_single(file, False)
        if root not in self.known_source:
            self.known_source.append(root)
        self.make_cache()

    def load_single(self, path, build_cache=True):
        try:
            m = ".".join(pathlib.Path(path).parts)[4:-3]
            importlib.import_module(m)
        except Exception as e:
            return False
        if build_cache:
            root = os.path.dirname(path)
            if root not in self.known_source:
                self.known_source.append(root)
            self.make_cache()
        return True

    def enumerate(self, dic=None):
        result = []
        if dic is None:
            dic = self.index_tree
        for item in dic.items():
            i = item[1]
            if type(i) == dict:
                result += self.enumerate(i)
            else:
                result.append(i)
        return result

    def make_cache(self):
        for s in self.signals:
            method = s["method"]
            function = s["func"]
            path = s["path"]
            auth = s["require_auth"]
            args = s["args"]
            docs = s["docs"]

            rt = path
            if rt.endswith(".py"):
                rt = rt[:-3]

            cursor = self.index_tree
            slt = rt.split("/")
            qt_paths = 0

            for i, part in enumerate(slt, 1):
                if part in cursor:
                    if i == len(slt):
                        if method in cursor[part]:
                            raise ValueError("Duplicate endpoint found:" + rt)
                else:
                    cursor[part] = {}

                cursor = cursor[part]

                if part == "__":
                    qt_paths += 1
            paths = 0

            for arg in args:
                if arg.arg_in == "path":
                    paths += 1
                elif arg.arg_in == "body" and method.upper() in ["GET", "HEAD", "TRACE", "OPTIONS"]:
                    raise TypeError("This method does not get a request body.")

            if paths != qt_paths:
                raise ValueError("Path argument count mismatch.")

            cursor[method] = EndPoint(method, rt, path, function, auth, args, bool(paths), docs)

    def get_endpoint(self, method, path, params=None):

        cursor = self.index_tree

        if path == "/":
            path = "_"

        if path.startswith("/"):
            path = path[1:]

        slt = path.split("/")
        args = []

        for i, part in enumerate(slt, 1):
            if part in cursor:
                cursor = cursor[part]
                continue

            if "__" in cursor:
                args.append(part)
                cursor = cursor["__"]
                continue

            return None

        if "_" in cursor:
            cursor = cursor["_"]

        if method in cursor:
            result = cursor[method]
            if result.path_arg:
                count = 0
                for arg in result.args:
                    if arg.arg_in == "path":
                        params[arg.name] = args[count]
                        count += 1
            return result

        return None

    def reload(self):
        self.signals.clear()
        self.index_tree.clear()
        for source in self.known_source:
            self.load(source)


__all__ = [
    "http", "Argument", "EndPoint", "Document", "Response", "Method"
]