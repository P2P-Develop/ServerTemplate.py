from __future__ import annotations

from typing import Optional, Any

import importlib
import os
import pathlib

from enum import Enum
from route import quick_invalid, write, Cause
from route import error as e


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
    def values() -> list:
        return [ev.value for ev in Method]

    def __radd__(self, other):
        return str(self) + "|" + str(other)

    def __and__(self, other):
        return str(self) + "|" + str(other)

    def __or__(self, other):
        return str(self) + "|" + str(other)

    def __str__(self):
        return self.value


class Document:
    def __init__(self,
                 title: str = None,  # title or summary required
                 summary: str = None,
                 # description: str = "Description",
                 # desc: str = "Description",
                 types: list | str = "application/octet-stream",
                 example: Any = None,
                 security: Optional[dict] = None,
                 responses: Optional[list] = None,
                 tags: Optional[list] = None,
                 format_type: Optional[str] = None,
                 **more_args):
        if title is None and summary is None:
            raise ValueError("Title or Summary must not be None.")
        self.title = summary if title is None else title
        # self.description = desc if description is None else description
        self.types = [types] if isinstance(types, str) else types
        self.example = example
        self.security = security
        self.more = more_args
        self.responses = [] if responses is None else responses
        self.tags = [] if tags is None else tags
        self.format = format_type


def http(method: str,
         require_auth: bool = True,
         args: tuple | list | Argument = (),
         docs: Optional[Document] = None):
    def _context(handler):
        path: Optional[str] = None
        file = handler.__globals__["__file__"]
        if "___" in os.path.normpath(file).split(os.path.sep):
            raise IsADirectoryError("Path-argument like directory found.")
        ep_dir = os.path.dirname(file)
        if file.endswith("___.py") and \
            len([name for name in os.listdir(ep_dir) if os.path.isfile(ep_dir + "/" + name)]) >= 2:
            raise FileExistsError("Endpoint conflict")

        for base in loader.known_source:
            if os.path.abspath(file).startswith(os.path.abspath(base)):
                path = os.path.relpath(file, os.path.relpath(base))

        if path is None:
            raise FileNotFoundError("Base path not found.")
        path = path.replace(os.sep, "/")
        pp = 0

        if isinstance(args, Argument):
            arg3 = (args,)
        else:
            arg3 = args

        for arg in arg3:
            if arg.arg_in == "path":
                if (path != "___" and path in "___") or "__" not in path:
                    raise ValueError("Can't routing to this endpoint.")

            if arg.arg_in == "path":
                pp += 1

        if isinstance(method, str):
            if method == "*":
                fig = method.split("|")
                for met in Method.values():
                    if met in fig:
                        continue
                    loader.signals.append({
                        "method": met,
                        "func": handler,
                        "path": path,
                        "require_auth": require_auth,
                        "args": arg3,
                        "docs": docs
                    })
                return
            if "|" in method:
                for met in method.split("|"):
                    loader.signals.append({
                        "method": met,
                        "func": handler,
                        "path": path,
                        "require_auth": require_auth,
                        "args": arg3,
                        "docs": docs
                    })
                return

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


class Documented:
    def __init__(self, document: Optional[Document] = None):
        self.docs = document


class Undefined: pass


class Argument(Documented):
    def __init__(self,
                 name: str,
                 arg_type: str,
                 arg_in: str,
                 required: bool = True,
                 auto_cast: bool = True,
                 minimum: int = -1,
                 maximum: int = -1,
                 must_be: tuple | list = (),
                 doc: Optional[Document] = None,
                 format_type: Optional[str] = None,
                 ignore_check_expect100: bool = False,
                 enum: tuple | list = (),
                 default: Any = Undefined):
        super().__init__(doc)
        if arg_type not in ["str", "string", "bool", "boolean", "number", "int", "long",
                            "double", "decimal", "float", "other"]:
            raise ValueError("Argument type is must be valid type.")
        if arg_in not in ["path", "query", "body"]:
            raise ValueError("Argument location is mut be valid type.")
        self.name = name
        self.type = arg_type
        self.arg_in = arg_in
        self.required = required
        self.auto_cast = auto_cast
        self.min = minimum
        self.max = maximum
        self.must_be = must_be if enum is None else enum
        self.document = doc
        self.format = format_type
        self.ignore_check_expect100 = ignore_check_expect100
        self.default = default

    def norm_type(self, val: Any = None) -> Any:
        if "str" in self.type:
            return "string" if val is None else str(val)
        elif "bool" in self.type:
            return "boolean" if val is None else bool(val)
        elif self.type is "number" or "int" in self.type:
            return "integer" if val is None else int(val)
        elif self.type is "long":
            return "integer" if val is None else int(val)
        else:
            return "number" if val is None else float(val)

    def validate(self, param_dict: dict) -> int:
        # NOT_FOUND = -1, OK = 0, NOT_MATCH = 1, TYPE_ERR = 2, MINIMUM_ERR = 3, MAXIMUM_ERR = 4
        name = self.name
        typ = self.type
        cast = self.auto_cast
        must_be = self.must_be
        min_val = self.min
        max_val = self.max

        if name not in param_dict:
            if self.default is not Undefined:
                param_dict[name] = self.norm_type(self.default)
                return 0
            if self.required:
                if self.ignore_check_expect100:
                    return 0
                return -1
            else:
                return 0

        value = param_dict[name]

        if "str" in typ:
            if len(must_be) is not 0 and value not in must_be:
                return 1

            if min_val is not -1 and len(value) < min_val:
                return 3

            if max_val is not -1 and len(value) > max_val:
                return 4

            if cast:
                param_dict[name] = str(value)

        elif "bool" in typ:
            if value not in ("true", "false") + tuple(self.must_be):
                return 1

            if cast:
                param_dict[name] = bool(value)
        elif typ == "other":
            return 0
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

            if min_val is not -1 and val < min_val:
                return 3

            if max_val is not -1 and val > max_val:
                return 4

            if cast:
                param_dict[name] = val

        return 0


class EndPoint(Documented):
    def __init__(self,
                 method: str,
                 route_path: str,
                 rel_path: str,
                 handler,
                 auth_required: bool = True,
                 args: Optional[list] = None,
                 path_arg: bool = False,
                 doc: Optional[Document] = None):
        super().__init__(doc)
        self.method = method
        self.route_path = route_path
        self.rel_path = rel_path
        self.handler = handler
        self.auth_required = auth_required
        self.args = () if args is None else args
        self.path_arg = path_arg

    def handle(self, handler, params: dict, queries: dict, path_param: dict) -> Any:
        if self.auth_required and handler.do_auth():
            return

        if not self.validate_arg(handler, params, queries, path_param):
            return

        return self.handler(handler, params)

    def validate_arg(self, handler, params: dict, queries: dict, path_param: dict) -> bool:

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
                continue
            elif code == 1:
                if "bool" in arg.type:
                    quick_invalid(handler, arg.name, "[" + ", ".join(("true", "false") + tuple(arg.must_be)) + "]")
                    return False
                else:
                    quick_invalid(handler, arg.name, "[" + ", ".join(arg.must_be) + "]")
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
            write(handler, 400, e(Cause.MISSING_FIELD, Cause.MISSING_FIELD[2]
                                  .replace("%0", str(len(missing)))
                                  .replace("%1", ", ".join(missing))))
            return False
        return True


class Response(Documented):
    def __init__(self,
                 code: int = 0,
                 body: Any = None,
                 raw_body: bool = False,
                 content_type: str | list = None,
                 headers: Optional[dict] = None,
                 doc: Optional[Document] = None):
        super().__init__(doc)
        self.code = code
        self.docs = doc
        self.headers = {} if headers is None else headers
        self.body_data = body
        self.raw = raw_body
        self.cont_type = content_type

    def header(self, name: str, value: str) -> Response:
        self.headers[name] = value
        return self

    def body(self, value: Any, raw: bool = False) -> Response:
        self.body_data = value
        self.raw = raw
        return self

    def content_type(self, value: str) -> Response:
        self.cont_type = value
        self.header("Content-Type", value)
        return self

    def get_code(self) -> int:
        return self.code


class SuccessResponse(Response):
    pass


class ErrorResponse(Response):
    def __init__(self,
                 cause: Optional[Cause] = None,
                 code: int = 0,
                 headers: Optional[dict] = None,
                 body: Any = None,
                 content_type: Optional[str | list] = None,
                 doc: Optional[Document] = None):
        if cause is not None:
            super().__init__(cause[0], headers, cause[2], content_type, headers, doc)
        else:
            super().__init__(code, body, False, content_type, headers, doc)

        self.cause = cause


def success(code) -> SuccessResponse:
    return SuccessResponse(code)


def error(cause: Optional[Cause] = None, code: int = 0, message: Optional[str] = None) -> ErrorResponse:
    if cause is not None:
        return ErrorResponse(cause)
    return ErrorResponse(code=code, body=message)


global loader


class EPManager:
    known_source: list[str]

    def __init__(self):
        global loader
        self.signals = []
        self.index_tree = {}
        self.known_source = []
        self.count = 0
        loader = self

    def load(self, root: str) -> None:
        if root in self.known_source:
            raise ValueError("Endpoint base already loaded.")
        else:
            self.known_source.append(root)

        for file in pathlib.Path(root).glob("**/*.py"):
            self.load_single(str(file), False)
        self.make_cache()

    def load_single(self, path: str, build_cache: bool = True) -> bool:
        try:
            m = ".".join(pathlib.Path(path).parts)[4:-3]
            importlib.import_module(m)
        except (ModuleNotFoundError, TypeError):
            return False
        if build_cache:
            root = os.path.dirname(path)
            if root not in self.known_source:
                self.known_source.append(root)
            self.make_cache()
        return True

    def enumerate(self, dic: Optional[dict] = None) -> list:
        result = []
        if dic is None:
            dic = self.index_tree
        for item in dic.items():
            i = item[1]
            if isinstance(i, dict):
                result += self.enumerate(i)
            else:
                result.append(i)
        return result

    def make_cache(self) -> None:
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

                if part == "__" or part == "___":
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
            self.count += 1

    def get_endpoint(self, method: str, path: str, params: dict = {}) -> Optional[EndPoint]:

        cursor = self.index_tree

        if path == "/":
            path = "_"

        if path.startswith("/"):
            path = path[1:]

        slt = path.split("/")
        args = []

        for i, part in enumerate(slt):
            if part in cursor:
                cursor = cursor[part]
                continue

            if "___" in cursor:
                args.append("/".join(slt[i:]))
                cursor = cursor["___"]
                break

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
        for source in list(self.known_source):
            self.known_source.remove(source)
            self.load(source)


__all__ = [
    "http", "Argument", "EndPoint", "Document", "Method", "success", "error",
    "SuccessResponse", "ErrorResponse", "Response"
]
