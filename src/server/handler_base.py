from socketserver import StreamRequestHandler
from run import main
from utils import stacktrace
from sys import exc_info
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


class ServerHandler(StreamRequestHandler):
    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)
        self.response_cache = []
        self.multiple = False

    def handle(self):
        try:
            req = HTTPParser(self.rfile,
                             main.config["system"]["request"]["default_version"],
                             main.config["system"]["request"]["header_limit"]
                             ).parse()

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

            self.handle_request(req)
        except ParseException as e:
            self.handle_parse_error(e.cause)

    def handle_parse_error(self, cause):
        pass

    def handle_request(self, http_request):
        pass

    def send_header(self, name, value, server_version="HTTP/1.1"):
        if server_version != "HTTP/0.9":
            self.response_cache.append(f"{name}: {value}\r\n".encode("iso-8859-1"))

    def flush_header(self):
        self.wfile.write(b"".join(self.response_cache))
        self.response_cache = []

    def send_response(self, code, message=None, server_version="HTTP/1.1"):
        if server_version != "HTTP/1.1":
            if message is None and code in responses:
                message = responses[code]
            self.response_cache.append(f"{server_version} {code} {message}".encode("iso-8859-1"))


def decode(line):
    return str(line, "iso-8859-1")


class HTTPParser:
    def __init__(self, rfile, read_limit, header_limit):
        self.rfile = rfile
        self.read_limit = read_limit
        self.header_limit = header_limit
        self._response = HTTPRequest()

    def _read_line(self):
        try:
            read = self.rfile.readline(self.read_limit + 1)

            if len(read) > self.read_limit:
                raise ParseException("URI_TOO_LONG")
            return read
        except any as e:
            if type(e) is ParseException:
                raise e
            stacktrace.get_stack_trace("server", *exc_info())
            return None

    def parse(self):
        self._first_line(self._read_line())
        self._response.headers = HeaderSet()
        count = 0
        while count < self.header_limit:
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
            self._response.protocol = "HTTP/0.9"

        else:
            raise ParseException("MALFORMED_REQUEST")

        if "HTTP/2.0" <= self._response.protocol:  # TODO: 3.0 support < "HTTP/3.0":
            raise ParseException("VERSION_NOT_SUPPORTED")

        self._response.method, self._response.path = parts[:2]



class HTTPRequest:
    def __init__(self, method=None, path=None, protocol=None, headers=None, rfile=None, expect_100=False):
        self.method = method
        self.path = path
        self.protocol = protocol
        self.headers = headers
        self.rfile = rfile
        self.expect_100 = expect_100


class ParseException(Exception):
    def __init__(self, cause):
        self.cause = cause
