import cgi
import json
import mimetypes
import os
import sys
import urllib.parse as parse
import endpoint
import route
from utils.stacktrace import get_stack_trace
from utils.logging import get_log_name
from server.handler_base import ServerHandler, HTTPRequest
from utils.guesser import guess


class Handler(ServerHandler):

    def __init__(self, request, client_address, server):
        self.logger = server.logger
        self.token = server.token
        self.instance = server.instance
        self.config = self.instance.config
        self.request = None
        super().__init__(request, client_address, server)

    def handle_request(self):
        self.handle_switch()
        if not self.wfile.closed:
            self.wfile.flush()
            self.wfile.close()

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

                    self.send_response(content["code"])
                    self.send_header("Content-Type", "application/json")
                    self.end_header()
                    self.wfile.write(json.JSONEncoder().encode(content["obj"]).encode("utf-8"))
                    return

            if os.path.exists("resources/resource" + path):
                if self.do_auth():
                    return

                with open("resources/resource" + path, mode="rb") as r:
                    self.send_response(200)
                    self.send_header("Content-Type", mimetypes.guess_type("resources/resource" + path)[0])
                    self.end_header()
                    self.wfile.write(r.read())
                    return

            route.post_error(self, route.Cause.EP_NOTFOUND)
        except Exception:
            get_stack_trace("server", *sys.exc_info())

    def dynamic_handle(self, path, params, queries):
        path_param = {}

        ep = endpoint.loader.get_endpoint(self.request.method, path, path_param)

        if ep is None:
            return False

        try:
            handled = ep.handle(self, params, queries, path_param)
        except Exception:
            get_stack_trace("handler_root", *sys.exc_info())
            return

        if handled is None:
            return True

        if issubclass(type(handled), endpoint.Response):
            if issubclass(type(handled), endpoint.ErrorResponse) and handled.cause is not None:
                self.send_response(handled.code, handled.cause[1])
            else:
                self.send_response(handled.code)

            for header in handled.headers.items():
                self.send_header(header[0], header[1])
            self.end_header()
            if handled.body_data is not None:
                self._send_body(handled.body_data, handled.raw, handled.cont_type)

        if handled is not None:
            self.send_response(200)
            self._send_body(handled)

        return True

    supported_type = {
        "application/x-www-form-urlencoded":
            lambda body, ct: (parse.urlencode(body) if isinstance(body, dict) else parse.quote(str(body))).encode("utf-8"),
        "application/json": lambda body, ct: json.JSONEncoder().encode(body).encode("utf-8"),
        "application/octet-stream": lambda body, ct: body
    }

    def write_type(self, body, content_type):
        n = content_type in self.supported_type
        if n:
            self.send_body(content_type, self.supported_type[content_type](body, content_type))

        return n

    def _send_body(self, body, raw=False, content_types=None):
        if raw:
            self.wfile.write(body)
            return

        default = self.config["system"]["request"]["default_content_type"]
        accept = self.request.headers["Accept"] if "Accept" in self.request.headers else ""

        if content_types is not None:
            if isinstance(content_types, str):
                self.write_type(body, guess(accept, [content_types], default))
                return
            elif isinstance(content_types, list) or isinstance(content_types, tuple):
                self.write_type(body, guess(accept, content_types, default))
                return
        self.write_type(body, guess(accept, self.supported_type.keys(), default))

    def send_body(self, content_type, body):
        self.send_header("Content-Length", len(body))
        self.send_header("Content-Type", content_type)
        self.end_header()
        self.wfile.write(body)

    def log_request(self, **kwargs):
        self.logger.info(get_log_name(), '%s -- %s %s -- "%s %s"' %
                         (kwargs["client"], kwargs["code"], "" if kwargs["message"] is None else kwargs["message"],
                          self.request.method, kwargs["path"]))

    def handle_switch(self):
        try:
            path = parse.urlparse(self.request.path)
            queries = dict(parse.parse_qsl(path.query))

            if self.request.method in ["GET", "HEAD", "TRACE", "OPTIONS"]:

                self.call_handler(path.path, {}, queries)
            else:
                if "Content-Type" in self.request.headers:
                    content_len = int(self.request.headers.get("content-length"))
                    content_type = self.request.headers["Content-Type"]

                    if content_type in ["application/json", "text/json", "application/x-json"]:
                        req_body = self.rfile.read(content_len).decode("utf-8")
                        args = json.JSONDecoder().decode(req_body)
                        if not isinstance(args, dict):
                            args = {}

                    elif content_type == "application/x-www-form-urlencoded":
                        req_body = self.rfile.read(content_len).decode("utf-8")
                        args = dict(parse.parse_qsl(req_body))

                    elif content_type.startswith("multipart/form-data"):
                        f = cgi.FieldStorage(fp=self.rfile,
                                             headers=self.request.headers,
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
        except Exception:
            get_stack_trace("server", *sys.exc_info())

    def do_auth(self):
        self.request: HTTPRequest
        if "Authorization" not in self.request.headers:
            route.post_error(self, route.Cause.AUTH_REQUIRED)

            return True

        auth = self.request.headers["Authorization"].split(" ")

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

    def handle_parse_error(self, cause):
        pass
