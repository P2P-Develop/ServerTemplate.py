import cgi
import json
import mimetypes
import os
import sys
import urllib.parse as parse
from http.server import BaseHTTPRequestHandler
import endpoint
import route
from utils.stacktrace import get_stack_trace
from utils.logging import get_log_name


def write(sv, code, txt):
    sv.send_response(code)
    sv.send_header("Content-Type", "application/json")
    sv.end_headers()
    sv.wfile.write(txt.encode())


class Handler(BaseHTTPRequestHandler):

    def __init__(self, request, client_address, server):
        self.logger = server.logger
        self.token = server.token
        self.instance = server.instance
        self.config = self.instance.config
        super().__init__(request, client_address, server)

    def log_message(self, format, *args):
        self.logger.info(get_log_name(), self.address_string() +
                         " -> " + format % args)

    def do_auth(self):
        if "Authorization" not in self.headers:
            route.post_error(self, route.Cause.AUTH_REQUIRED)

            return True

        auth = self.headers["Authorization"].split(" ")

        if len(auth) != 2:
            route.post_error(self, route.Cause.AUTH_REQUIRED)

            return True

        if str(auth[0]).lower() != "token":
            route.post_error(self, route.Cause.AUTH_REQUIRED)

            return True

        if not self.token.validate(auth[1]):
            route.post_error(self, route.Cause.AUTH_REQUIRED)

            return True
        return False

    def call_handler(self, path: str, params, queries):

        if ".." in path:
            route.post_error(self, route.Cause.EP_NOTFOUND)

            return

        if self.dynamic_handle(path, params, queries):
            return

        try:
            if os.path.exists("resources/handle" + path + ".txt"):
                with open("resources/handle" + path + ".txt", encoding="utf-8", mode="r") as r:
                    content = r.read().split("\n")
                    route.success(self, int(content[0]), content[1:])
                    return

            if os.path.exists("resources/handle" + path + ".json"):
                with open("resources/handle" + path + ".json", encoding="utf-8", mode="r") as r:
                    content = json.JSONDecoder().decode(r.read())
                    if content["auth"]:
                        if self.do_auth():
                            return

                    write(self, content["code"], json.JSONEncoder().encode(content["obj"]))
                    return

            if os.path.exists("resources/resource" + path):
                if self.do_auth():
                    return

                with open("resources/resource" + path, mode="rb") as r:
                    self.send_response(200)
                    self.send_header("Content-Type", mimetypes.guess_type("resources/resource" + path)[0])
                    self.end_headers()
                    self.wfile.write(r.read())
                    return

            route.post_error(self, route.Cause.EP_NOTFOUND)
        except Exception as e:
            get_stack_trace("server", *sys.exc_info())
            pass

    def dynamic_handle(self, path, params, queries):
        path_param = {}

        ep = endpoint.loader.get_endpoint(self.command, path, path_param)

        if ep is None:
            return False

        handled = ep.handle(self, params, queries, path_param)

        if handled is None:
            return True

        if issubclass(type(handled), endpoint.Response):
            if issubclass(type(handled), endpoint.ErrorResponse) and handled.cause is not None:
                self.send_response(handled.code, handled.cause[1])
            else:
                self.send_response(handled.code)

            for header in handled.headers.items():
                self.send_header(header[0], header[1])
            self.end_headers()

        if handled.body is not None:
            self.send_body(handled.body, handled.raw)

        return True

    def send_body(self, body, raw):
        if raw:
            self.wfile.write(body)
            return

        if "Accept" not in self.headers and "accept" not in self.headers:
            self.wfile.write(json.dumps(body).encode("utf-8"))
            return

        accept = self.headers["Accept"] if "Accept" in self.headers else self.headers["accept"]

        if "application/x-www-form-urlencoded" in accept:
            if type(body) is dict:
                self.wfile.write(parse.urlencode(body, True).encode("utf-8"))
            elif type(body) is bytes:
                self.wfile.write(body)
            else:
                self.wfile.write(parse.quote(body).encode("utf-8"))
        elif True or "application/json" in accept or "text/json" in accept:  # TODO: More options
            if type(body) is not bytes:
                self.wfile.write(json.dumps(body).encode("utf-8"))
            else:
                self.wfile.write(body)

    def handle_switch(self):
        try:
            path = parse.urlparse(self.path)
            queries = dict(parse.parse_qsl(path.query))

            if self.command in ["GET", "HEAD", "TRACE", "OPTIONS"]:

                self.call_handler(path.path, {}, queries)
            else:
                if "Content-Type" in self.headers:
                    content_len = int(self.headers.get("content-length"))
                    content_type = self.headers["Content-Type"]

                    if content_type in ["application/json", "text/json", "application/x-json"]:
                        req_body = self.rfile.read(content_len).decode("utf-8")
                        args = json.JSONDecoder().decode(req_body)
                        if type(args) != dict:
                            args = {}

                    elif content_type == "application/x-www-form-urlencoded":
                        req_body = self.rfile.read(content_len).decode("utf-8")
                        args = dict(parse.parse_qsl(req_body))

                    elif content_type.startswith("multipart/form-data"):
                        f = cgi.FieldStorage(fp=self.rfile,
                                             headers=self.headers,
                                             environ={
                                                 "REQUEST_METHOD": "POST",
                                                 "CONTENT_TYPE": content_type,
                                             },
                                             encoding="utf-8")
                        args = {}
                        for fs in f.keys():
                            args[fs] = f.getvalue(fs)

                    else:
                        route.quick_invalid(self, "Content-Type header", "valid header")
                        return
                        # args = self.rfile.read(content_len).decode("utf-8")

                    self.call_handler(path.path, args, queries)
                else:
                    route.post_error(self, route.Cause.MISSING_FIELD, "Content-Type header is required.")
                    return
        except:
            get_stack_trace("server", *sys.exc_info())

    def handle_one_request(self):
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(414)
                return
            if not self.raw_requestline:
                self.close_connection = True
                return
            if not self.parse_request():
                return
            self.handle_switch()
            if not self.wfile.closed:
                self.wfile.flush()
                self.wfile.close()
        except Exception as e:
            get_stack_trace("server", *sys.exc_info())
            self.close_connection = True
            return

    def send_response(self, code, message=None):
        self.log_request(code)
        self.send_response_only(code, message)
        self.send_header("Server", "gws")
        self.send_header("Connection", "close")
