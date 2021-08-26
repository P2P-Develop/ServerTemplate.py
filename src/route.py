import json
import os
from enum import Enum

from server import ep


def encode(amfs):
    return json.JSONEncoder().encode(amfs)


def write(sv, code, txt):
    sv.send_response(code)
    sv.send_header("Content-Type", "application/json")
    sv.end_headers()
    sv.wfile.write(txt.encode())


class Cause:
    AUTH_REQUIRED = [401, "AUTHORIZATION_REQUIRED", "Authorization required."]
    NOT_ALLOWED_OPERATION = [
        405, "OPERATION_NOT_ALLOWED", "Operation not allowed."]
    UNSUPPORTED_OPERATION = [
        400, "OPERATION_UNSUPPORTED", "Operation not supported."]
    FORBIDDEN = [403, "FORBIDDEN", "Access denied."]
    EP_NOTFOUND = [404, "E_NOTFOUND", "Endpoint not found."]
    GONE = [410, "GONE", "Resource has already gone."]
    MISSING_FIELD = [400, "MISSING_FIELD", "Missing %0 field(s): [%1]"]
    INVALID_FIELD = [400, "INVALID_FIELD",
                     "Invalid field: Field %0 is must be %1."]
    INVALID_FIELD_UNK = [400, "INVALID_FIELD", "Invalid field has found."]
    ERROR_OCCURRED = [500, "ERROR_OCCURRED", "An error has occurred."]


def validate(handler, fname, value, must):
    if str(value) in must:
        return False

    write(handler, 400, error(Cause.INVALID_FIELD, Cause.INVALID_FIELD[2]
                              .replace("%0", fname)
                              .replace("%1", ", ".join(must))))
    return True


def missing(handler, fields, require):
    diff = search_missing(fields, require)
    if len(diff) is 0:
        return False
    write(handler, 400, error(Cause.MISSING_FIELD, Cause.MISSING_FIELD[2]
                              .replace("%0", str(len(diff)))
                              .replace("%1", ", ".join(diff))))
    return True


def success(handler, code, obj):
    write(handler, code, encode({
        "success": True,
        "result": obj
    }))


def post_error(handler, cause):
    write(handler, cause[0], error(cause))


def search_missing(fields, require):
    for key in fields.keys():
        if key in require:
            require.remove(key)
    return require


def error(cause, message=None):
    if message is None:
        return encode({
            "success": False,
            "cause": cause[1],
            "message": cause[2]
        })
    else:
        return encode({
            "success": False,
            "cause": cause[1],
            "message": message
        })


def cerror(cause, message):
    return encode({
        "success": False,
        "cause": cause,
        "message": message
    })


def wssuccess():
    return encode({
        "success": True
    })


def finish(handler):
    handler.finish()
    handler.connection.close()


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


def quick_invalid(handler, name, message):
    write(handler, 400, error(Cause.INVALID_FIELD, Cause.INVALID_FIELD[2]
                              .replace("%0", name)
                              .replace("%1", message)))


def http(method, require_auth=True, args=()):
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

        ep.loader.signals.append({
            "method": method,
            "func": handler,
            "path": path,
            "require_auth": require_auth,
            "args": arg3
        })
        return handler

    return _context


__all__ = [
    "write", "Cause", "validate", "missing", "success", "post_error",
    "finish", "Method", "http", "quick_invalid"
]
