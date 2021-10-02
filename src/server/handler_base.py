from socket import socket
from typing import Optional, BinaryIO
from socketserver import StreamRequestHandler
from utils.stacktrace import get_stack_trace
from utils.logging import get_log_name
from utils.header_parse import HeaderSet
import sys


responses = {
    100: "Continue",
    101: "Switching Protocol",
    102: "Processing",
    103: "Early Hints",

    200: "OK",
    201: "Created",
    203: "Non-Authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    207: "Multi-Status",
    208: "Already Reported",
    226: "IM Used",

    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy",
    306: "Switch Proxy",  # Unused
    307: "Temporary Redirect",
    308: "Permanent Redirect",

    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Payload Too Large",
    414: "URI Too Long",
    415: "Unsupported Media Type",
    416: "Range Not Satisfiable",
    417: "Expectation Failed",
    418: "I'm a teapot",
    421: "Misdirected Request",
    422: "Unprocessable Entity",
    423: "Locked",
    424: "Failed Dependency",
    425: "Too Early",
    426: "Upgrade Required",
    428: "Precondition Required",
    429: "Too Many Requests",
    431: "Request Header Fields Too Large",
    451: "Unavailable For Legal Reasons",

    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported",
    506: "Variant Also Negotiates",
    507: "Insufficient Storage",
    508: "Loop Detected",
    510: "Not Extended",
    511: "Network Authentication Required"
}

default_version = "HTTP/0.9"
read_limit = 65536
header_limit = 100


class AbstractHandlerBase(StreamRequestHandler):
    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)

    def handle(self) -> None:
        pass

    def handle_parse_error(self, cause: str) -> None:
        pass

    def handle_request(self) -> None:
        pass

    def send_header(self, name: str, value: any, server_version: str) -> None:
        pass

    def flush_header(self) -> None:
        pass

    def end_header(self) -> None:
        pass

    def send_response(self, code: int, message: str, server_version: str) -> None:
        pass

    def send_body(self, content_type: str, raw_body: bytes) -> None:
        pass

    def log_request(self, **kwargs) -> None:
        pass


class CachedHeader(AbstractHandlerBase):
    def __init__(self):
        self._response_cache = []

    def send_header(self, name: str, value: any, server_version: str = "HTTP/1.1") -> None:
        if server_version != "HTTP/0.9":
            self._response_cache.append(f"{name}: {str(value)}\r\n".encode("iso-8859-1"))

    def flush_header(self) -> None:
        if not hasattr(self, "_response_cache"):
            return
        self.wfile.write(b"".join(self._response_cache))
        self._response_cache = []

    def end_header(self) -> None:
        if not hasattr(self, "_response_cache"):
            self._response_cache = []
        if len(self._response_cache) > 1:
            self._response_cache.append(b"\r\n")
        self.flush_header()

    def send_response(self, code: int, message: str = None, server_version: str = "HTTP/1.1") -> None:
        if server_version != "HTTP/0.9":
            if message is None and code in responses:
                message = responses[code]
            if not hasattr(self, "response_cache"):
                self._response_cache = []
            self._response_cache.append(f"{server_version} {code} {message}\r\n".encode("iso-8859-1"))


class ServerHandler(CachedHeader, AbstractHandlerBase):
    def __init__(self, request: socket, client_address: tuple, server):
        CachedHeader.__init__(self)
        self.response_cache = []
        self.multiple = False
        self.request = None
        self._code = 0
        self._message = None

        AbstractHandlerBase.__init__(self, request, client_address, server)

    def handle(self) -> None:
        self._handle()

    def _handle(self) -> None:
        try:
            req = HTTPParser(self, self.rfile).parse()

            if not req:
                return

            if req.protocol >= "HTTP/1.1":
                self.multiple = True

            if "Connection" in req.headers:
                if req.headers["Connection"] == "keep-alive":
                    self.multiple = True
                elif req.headers["Connection"] == "close":
                    self.multiple = False

            if "Expect" in req.headers:
                if req.headers["Expect"] == "100-continue":
                    req.expect_100 = True

            self.request = req

            self.handle_request()

            if self._message is None and self._code in responses:
                self._message = responses[self._code]

            self.log_request(code=self._code,
                             client="%s:%s" % self.client_address,
                             message=self._message,
                             path=req.path)

        except ParseException as e:
            self.handle_parse_error(e.cause)

    def send_header(self, name: str, value: any, server_version: str = "HTTP/1.1"):
        if name == "Connection":
            if value.lower() == "keep-alive":
                self.multiple = True
            elif value.lower() == "close":
                self.multiple = False

        super().send_header(name, value, server_version)

    def send_response(self, code, message: str = None, server_version: str = "HTTP/1.1") -> None:
        self._code = code
        self._message = message
        super().send_response(code, message, server_version)

    def send_body(self, content_type: str, raw_body: bytes) -> None:
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", len(raw_body))
        self.end_header()
        self.wfile.write(raw_body)


def decode(line: bytes) -> str:
    return str(line, "iso-8859-1")


class HTTPRequest:
    def __init__(self, handler, method: str = None, path: str = None, protocol: str = None,
                 headers: HeaderSet = None, rfile: BinaryIO = None, expect_100: bool = False,
                 parameters: dict = None):
        self.handler = handler
        self.method = method
        self.path = path
        self.protocol = protocol
        self.headers = headers
        self.rfile = rfile
        self.expect_100 = expect_100
        self.param = parameters


class HTTPParser:
    def __init__(self, handler: AbstractHandlerBase, rfile: BinaryIO):
        self.rfile = rfile
        self._response = HTTPRequest(handler)

    def _read_line(self) -> Optional[bytes]:
        try:
            read = self.rfile.readline(read_limit + 1)

            if not read:
                return

            if len(read) > read_limit:
                raise ParseException("URI_TOO_LONG")
            return read
        except Exception as e:
            if isinstance(e, ParseException):
                raise e
            print(get_log_name(), get_stack_trace("server", *sys.exc_info()))
            return

    def parse(self) -> Optional[HTTPRequest]:
        b = self._read_line()
        if not b:
            return
        self._first_line(b)
        self._response.headers = HeaderSet()
        count = 0
        while count < header_limit:
            b = self._read_line()
            if not b:
                return
            d = decode(b)

            if d == "\r\n":
                break

            self._header(d.rstrip("\r\n"))
            count += 1
        return self._response

    def _header(self, data: str) -> None:
        kv = data.split(":", 1)
        if len(kv) != 2:
            raise ParseException("MALFORMED_HEADER")

        self._response.headers.add(*kv)

    def _first_line(self, byte: bytes) -> None:
        line = decode(byte)
        parts = line.rstrip("\r\n").split()

        if len(parts) == 3:
            version = parts[-1]
            if not version.startswith("HTTP/"):
                raise ParseException("BAD_PROTOCOL")
            self._response.protocol = version

        elif len(parts) == 2:
            self._response.protocol = default_version

        else:
            raise ParseException("MALFORMED_REQUEST")

        if "HTTP/2.0" <= self._response.protocol:  # TODO: 3.0 support < "HTTP/3.0":
            raise ParseException("VERSION_NOT_SUPPORTED")

        self._response.method, self._response.path = parts[:2]


class ParseException(Exception):
    def __init__(self, cause):
        self.cause = cause
