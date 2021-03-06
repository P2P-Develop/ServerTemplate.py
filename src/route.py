import enum
import json
from server.handler_base import AbstractHandlerBase


# This code is deprecated in new futures.


def encode(amfs: any) -> str:
    return json.JSONEncoder().encode(amfs)


def write(handler, code: int, txt: str, content_type: str = "application/json") -> None:
    handler.send_response(code)
    handler.send_header("Content-Type", content_type)
    ln = txt.encode("utf-8")
    handler.send_header("Content-Length", len(ln))
    handler.end_header()
    handler.wfile.write(ln)


class Cause(enum.Enum):
    AUTH_REQUIRED = [401, "AUTHORIZATION_REQUIRED", "Authorization required."]
    NOT_ALLOWED_OPERATION = [
        405, "OPERATION_NOT_ALLOWED", "Operation not allowed."]
    UNSUPPORTED_OPERATION = [
        400, "OPERATION_UNSUPPORTED", "Operation not supported."]
    FORBIDDEN = [403, "FORBIDDEN", "Access denied."]
    EP_NOTFOUND = [404, "E_NOTFOUND", "Endpoint not found."]
    RESOURCE_NOTFOUND = [404, "RESOURCE_NOTFOUND", "Resource not found."]
    GONE = [410, "GONE", "Resource has already gone."]
    MISSING_FIELD = [400, "MISSING_FIELD", "Missing %0 field(s): [%1]"]
    PAYLOAD_EMPTY = [400, "PAYLOAD_EMPTY", "Payload empty."]
    INVALID_FIELD = [400, "INVALID_FIELD",
                     "Invalid field: Field %0 is must be %1."]
    INVALID_FIELD_UNK = [400, "INVALID_FIELD", "Invalid field has found."]
    ERROR_OCCURRED = [500, "ERROR_OCCURRED", "An error has occurred."]
    MALFORMED = [400, "MALFORMED_REQUEST", "Request malformed."]
    PROCESSING = [503, "PROCESSING", "Processing request."]
    SIZE_OVER = [413, "PAYLOAD_TOO_LARGE", "Payload too large."]
    INTERNAL_ERR = [500, "INTERNAL_ERROR", "Internal server error has occurred."]
    MISMATCH = [506, "MISMATCH", "Server files mismatch."]
    NOT_FOUND = [404, "NOT_FOUND", "Resource not found."]
    ALREADY_EXISTS = [409, "ALREADY_EXISTS", "Resource already exists."]

    def __getitem__(self, index):
        return self.value[index]


def validate(handler, fname: str, value: any, must: str) -> bool:
    if str(value) in must:
        return False

    write(handler, 400, error(Cause.INVALID_FIELD, Cause.INVALID_FIELD[2]
                              .replace("%0", fname)
                              .replace("%1", ", ".join(must))))
    return True


def missing(handler, fields: dict, require: list) -> bool:
    diff = search_missing(fields, require)
    if len(diff) == 0:
        return False
    write(handler, 400, error(Cause.MISSING_FIELD, Cause.MISSING_FIELD[2]
                              .replace("%0", str(len(diff)))
                              .replace("%1", ", ".join(diff))))
    return True


def success(handler, code: int, obj: any):
    write(handler, code, encode({
        "success": True,
        "result": obj
    }))


def post_error(handler, cause: Cause, message: str = None) -> None:
    write(handler, cause[0], error(cause, message))


def search_missing(fields: dict, require: list) -> list:
    for key in fields.keys():
        if key in require:
            require.remove(key)
    return require


def error(cause: Cause, message: str = None) -> str:
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


def cerror(cause, message) -> str:
    return encode({
        "success": False,
        "cause": cause,
        "message": message
    })


def wssuccess() -> str:
    return encode({
        "success": True
    })


def finish(handler: AbstractHandlerBase):
    handler.finish()
    handler.connection.close()


def quick_invalid(handler: AbstractHandlerBase, name: str, message: str):
    write(handler, 400, error(Cause.INVALID_FIELD, Cause.INVALID_FIELD[2]
                              .replace("%0", name)
                              .replace("%1", message)))


__all__ = [
    "write", "Cause", "validate", "missing", "success", "post_error",
    "finish", "quick_invalid", "error"
]
