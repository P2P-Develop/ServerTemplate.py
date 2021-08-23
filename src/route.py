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
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"

    HEAD = "HEAD"
    CONNECT = "CONNECT"
    OPTIONS = "OPTIONS"

    @staticmethod
    def values():
        return [e.value for e in Method]

def require_auth(func):
    def context(handler, path, params):
        if handler.do_auth():
            return
        func(handler, path, params)
    return context

def EndPoint(method, require_args=None, no_auth=False):
    def _a(func):
        def _b():
            if type(method) == Method:
                m2 = method.value.upper()
            else:
                m2 = str(method.upper())

            ep.loader.signals.append({
                "mod": __file__.replace(os.sep, "/")[4:-3],
                "method": m2,
                "func": func,
                "require_args": require_args if require_args is None else [],
                "no_auth": no_auth
            })
        return _b
    return _a

__all__ = [
    "write", "Cause", "validate", "missing", "success", "post_error", "finish", "Method", "EndPoint"
]
