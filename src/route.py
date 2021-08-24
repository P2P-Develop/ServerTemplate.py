import json
from enum import Enum


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


def quick_invalid(handler, name, message):
    write(handler, 400, error(Cause.INVALID_FIELD, Cause.INVALID_FIELD[2]
                              .replace("%0", name)
                              .replace("%1", message)))


def validate_arg(name, arg_type, min_value=-1, max_value=-1, missing_ok=False, do_cast=True, *must_be):
    if arg_type not in ["str", "string", "bool", "boolean", "number", "int", "double", "decimal", "float"]:
        raise ValueError("arg_type is must be " +
                         ", ".join(["str", "string", "bool", "boolean", "number", "int", "double", "decimal", "float"]))

    def context(func):
        def _context(handler, path, params):
            if name not in params and not missing_ok:
                raise ValueError(f"Parameter '{name}' is not in parameters. "
                                 "Set missing_ok to True, or use @route.require_args annotation.")

            value = params[name]

            if "str" in arg_type:
                if len(must_be) is not 0 and value not in must_be:
                    quick_invalid(handler, name, ", ".join(must_be))
                    return

                if min_value is not -1 and len(value) < min_value:
                    quick_invalid(handler, name, f"at least {min_value} character")
                    return

                if max_value is not -1 and len(value) > max_value:
                    quick_invalid(handler, name, f"less than {max_value} character")
                    return
                if do_cast:
                    params[name] = str(value)

            elif "bool" in arg_type:
                if value not in ("true", "false") + must_be:
                    quick_invalid(handler, name, " or ".join(("true", "false") + must_be))
                    return

                if do_cast:
                    params[name] = bool(value)

            else:
                val = None
                try:
                    if "int" in arg_type or arg_type == "number":
                        val = int(value)
                    else:
                        val = float(value)
                except ValueError:
                    quick_invalid(handler, name, arg_type)

                if len(must_be) is not 0 and val not in must_be:
                    quick_invalid(handler, name, ", ".join(must_be))
                    return

                if min_value is not -1 and val < min_value:
                    quick_invalid(handler, name, f"at least {min_value}")
                    return

                if max_value is not -1 and val > max_value:
                    quick_invalid(handler, name, f"less than {max_value}")
                    return

                if do_cast:
                    params[name] = val

            func(handler, path, params)

        return _context

    return context


def require_args(*args):
    def context(func):
        def _context(handler, path, params):
            if missing(handler, params, list(args)):
                return
            func(handler, path, params)

        return _context

    return context


def require_auth(func):
    def context(handler, path, params):
        if handler.do_auth():
            return
        func(handler, path, params)

    return context


__all__ = [
    "write", "Cause", "validate", "missing", "success", "post_error",
    "finish", "Method", "require_args", "require_auth", "validate_arg"
]
