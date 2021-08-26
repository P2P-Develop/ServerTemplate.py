import cgi
import json
import mimetypes
import os
import sys
import threading
import traceback
import urllib.parse as parse
from http.server import BaseHTTPRequestHandler

import route
import server.ep as ep


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

    @staticmethod
    def parse_thread_name(name):
        name = str.strip(name, "ThreadPoolExecutor-")
        splittext = str.split(name, "_")

        return f"thread-{splittext[0]}-{splittext[1]}"

    def get_log_name(self):
        return self.parse_thread_name(threading.current_thread().getName())

    def log_message(self, format, *args):
        self.logger.info(self.get_log_name(), self.address_string() +
                         " -> " + format % args)

    def do_auth(self):
        if self.path == "/docs.html":
            self.call_handler("/docs.html", None)

            return True

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

    def call_handler(self, path: str, params):

        if ".." in path:
            route.post_error(self, route.Cause.EP_NOTFOUND)

            return

        if self.dynamic_handle(path, params):
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
            self.print_stack_trace(*sys.exc_info())
            pass

    def dynamic_handle(self, path, params):
        endpoint = ep.loader.get_endpoint(self.command, path, params)

        if endpoint is None:
            return False

        endpoint.handle(self, params)

        return True

    def handle_switch(self):
        try:
            path = parse.urlparse(self.path)
            queries = parse.parse_qs(path.query)
            for param in list(queries.keys()):
                queries[param] = queries[param][0]

            if self.command in ["GET", "HEAD", "TRACE", "OPTIONS"]:

                self.call_handler(path.path, queries)
            else:
                if "Content-Type" in self.headers:
                    content_len = int(self.headers.get("content-length"))
                    content_type = self.headers["Content-Type"]

                    if content_type in ["application/json", "text/json", "application/x-json"]:
                        req_body = self.rfile.read(content_len).decode("utf-8")
                        args = json.JSONDecoder().decode(req_body)

                    elif content_type == "application/x-www-form-urlencoded":
                        req_body = self.rfile.read(content_len).decode("utf-8")
                        args = parse.parse_qs(req_body)

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
                        args = self.rfile.read(content_len).decode("utf-8")

                    self.call_handler(path.path, dict(queries, args))
                else:
                    self.call_handler(path.path, {})
        except:
            self.print_stack_trace(*sys.exc_info())

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
            self.print_stack_trace(*sys.exc_info())
            self.close_connection = True
            return

    def send_response(self, code, message=None):
        self.log_request(code)
        self.send_response_only(code, message)
        self.send_header("Server", "gws")
        self.send_header("Connection", "close")

    def print_stack_trace(self, etype, exception, trace):
        tb = traceback.TracebackException(etype, exception, trace)

        st = f"Unexpected exception while handling client request resource {self.path}\n"

        flag = False

        for stack in tb.stack:
            stack: traceback.FrameSummary
            if "handler_root" in stack.filename and not flag:
                flag = True
                st += "Caused by: " + self.get_class_chain(etype) + ": " + str(tb) + "\n"
            st += self.build_trace(stack)

        if not flag:
            st = f"Unexpected exception while handling client request resource {self.path}\n"
            for stack in tb.stack[:len(tb.stack) - 1]:
                st += self.build_trace(stack)
            st += "Caused by: " + self.get_class_chain(etype) + ": " + str(tb) + "\n"
            stack = tb.stack[len(tb.stack) - 1]
            st += self.build_trace(stack)

        self.logger.warn(self.parse_thread_name(threading.current_thread().getName()), st)

    @staticmethod
    def build_trace(stack):
        return "        at " + Handler.normalize_file_name(stack.filename) + "." + stack.name \
               + "(" + os.path.basename(stack.filename) + ":" + str(stack.lineno) \
               + "): " + stack.line + "\n"

    @staticmethod
    def normalize_file_name(path: str):
        das = path.split("src")
        del das[0]
        da = "".join(das)
        da = da.replace("\\", ".").replace("/", ".")
        return da[1:-3]

    @staticmethod
    def get_class_chain(clazz):
        mod = clazz.__module__
        if mod == "builtins":
            return clazz.__qualname__
        return f"{mod}.{clazz.__qualname__}"
