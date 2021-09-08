from socketserver import StreamRequestHandler
from sys import exc_info

from utils import stacktrace
from utils.header_parse import HeaderSet

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


class AbstractHandlerBase:
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


class CachedHeader(AbstractHandlerBase):
    def __init__(self):
        self.wfile = None
        self._response_cache = []

    def send_header(self, name, value, server_version="HTTP/1.1"):
        if server_version != "HTTP/0.9":
            self._response_cache.append(f"{name}: {str(value)}\r\n".encode("iso-8859-1"))

    def flush_header(self):
        if not hasattr(self, "_response_cache"):
            return
        self.wfile.write(b"".join(self._response_cache))
        self._response_cache = []

    def end_header(self):
        if not hasattr(self, "_response_cache"):
            self._response_cache = []
        self._response_cache.append(b"\r\n")
        self.flush_header()

    def send_response(self, code, message=None, server_version="HTTP/1.1"):
        if server_version != "HTTP/0.9":
            if message is None and code in responses:
                message = responses[code]
            if not hasattr(self, "response_cache"):
                self._response_cache = []
            self._response_cache.append(f"{server_version} {code} {message}\r\n".encode("iso-8859-1"))


class ServerHandler(StreamRequestHandler, CachedHeader, AbstractHandlerBase):
    def __init__(self, request, client_address, server):
        CachedHeader.__init__(self)
        self.response_cache = []
        self.multiple = False
        self.request = None
        StreamRequestHandler.__init__(self, request, client_address, server)

    def handle(self):
        self._handle()

    def _handle(self):
        try:
            req = HTTPParser(self, self.rfile).parse()

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
        except ParseException as e:
            self.handle_parse_error(e.cause)

    def send_header(self, name, value, server_version="HTTP/1.1"):
        if name == "Connection":
            if value.lower() == "keep-alive":
                self.multiple = True
            elif value.lower() == "close":
                self.multiple = False

        super().send_header(name, value, server_version)


def decode(line):
    return str(line, "iso-8859-1")


class HTTPParser:
    def __init__(self, handler, rfile):
        self.rfile = rfile
        self._response = HTTPRequest(handler)

    def _read_line(self):
        try:
            read = self.rfile.readline(read_limit + 1)

            if len(read) > read_limit:
                raise ParseException("URI_TOO_LONG")
            return read
        except Exception as e:
            if type(e) is ParseException:
                raise e
            stacktrace.get_stack_trace("server", *exc_info())
            return None

    def parse(self):
        self._first_line(self._read_line())
        self._response.headers = HeaderSet()
        count = 0
        while count < header_limit:
            d = decode(self._read_line())

            if d == "\r\n":
                break

            self._header(d.rstrip("\r\n"))
            count += 1
        return self._response

    def _header(self, data):
        kv = data.split(":", 1)
        if len(kv) != 2:
            raise ParseException("MALFORMED_HEADER")

        self._response.headers.add(*kv)

    def _first_line(self, byte):
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


class HTTPRequest:
    def __init__(self, handler, method=None, path=None, protocol=None,
                 headers=None, rfile=None, expect_100=False, parameters=None):
        self.handler = handler
        self.method = method
        self.path = path
        self.protocol = protocol
        self.headers = headers
        self.rfile = rfile
        self.expect_100 = expect_100
        self.param = parameters


class ParseException(Exception):
    def __init__(self, cause):
        self.cause = cause
