import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from socketserver import ThreadingTCPServer

from run import Main
from server.handler import Handler
from utils.logging import Logger
from utils.token import Token


class Server(ThreadingTCPServer, object):
    logger: Logger
    token: Token
    instance: Main
    thread: threading.Thread

    def __init__(self, address, handler, workers):
        super().__init__(address, handler)

        self.executor = ThreadPoolExecutor(max_workers=workers)

    def process_request(self, request, client_address):
        self.executor.submit(self.process_request_thread, request, client_address)

    def server_close(self):
        super().server_close()
        self.executor.shutdown(wait=True)

    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)


def startServer(instance, port, logger, token):
    with Server(("", port), Handler, 4) as server:
        server.logger = logger
        server.token = token
        server.instance = instance
        server.allow_reuse_address = True

        try:
            server.serve_forever()
        except SystemExit:
            pass
        finally:
            server.server_close()


def bind(port, instance, logger, token):
    thread = threading.Thread(target=startServer, args=(
        instance, port, logger, token))
    thread.daemon = True
    thread.start()
    logger.info("server", "Listening on 0.0.0.0:" + str(port))
