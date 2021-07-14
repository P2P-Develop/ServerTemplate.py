from http.server import BaseHTTPRequestHandler
import os
from utils import result
import urllib.parse as parse
import sys
import threading
from importlib import import_module


def grand(sv, path, data):
    p = "public/html" + path
    if os.path.exists(p):
        with open(p, "rb") as obj:
            sv.send_response(200)
            sv.end_headers()
            sv.wfile.write(obj.read())
        return True
    return False


def text(path, replaces):
    with open("public/html" + path, "r", encoding="utf-8") as r:
        txt = r.read()
    for replace in replaces:
        txt = txt.replace("%%" + replace[0] + "%%", replace[1])
    return


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

    def parse_thread_name(self, name):
        name = str.strip(name, "ThreadPoolExecutor-")
        splittext = str.split(name, "_")

        return f"thread-{splittext[0]}-{splittext[1]}"

    def log_message(self, format, *args):
        self.logger.info(self.parse_thread_name(threading.current_thread().getName()), self.address_string() + " -> " + format % args)

    def do_GET(self):
        if "Authorization" not in self.headers:
            result.qe(self, result.Cause.AUTH_REQUIRED)

            return

        try:
            path = parse.urlparse(self.path)
            params = parse.parse_qs(path.query)

            auth = self.headers["Authorization"].split(" ")

            if len(auth) != 2:
                result.qe(self, result.Cause.AUTH_REQUIRED)

                return

            if str(auth[0]).lower() != "token":
                result.qe(self, result.Cause.AUTH_REQUIRED)

                return

            if not self.token.validate(auth[1]):
                result.qe(self, result.Cause.AUTH_REQUIRED)

                return

            self.handleRequest(path, params)
        except Exception as e:
            tb = sys.exc_info()[2]

            self.logger.error(self.parse_thread_name(threading.current_thread().getName()),
                               "An error has occurred while processing request from client: {0}"
                               .format(e.with_traceback(tb)))

    def handleRequest(self, path, params):
        p = path.path.replace("/", ".")

        if p.endswith("."):
            p = p[:-1]

        try:
            handler = import_module("server.handler_root" + p)

            handler.handle(self, path, params)
        except ModuleNotFoundError and AttributeError:
            try:
                handler = import_module("server.handler_root" + p + "._")

                handler.handle(self, path, params)
            except ModuleNotFoundError:
                result.qe(self, result.Cause.EP_NOTFOUND)
