from socketserver import ThreadingTCPServer
from run import Main
from server.handler import Handler
import socket
from ssl import wrap_socket
import threading

from utils.logging import Logger
from utils.token import Token


class Server(ThreadingTCPServer, object):
    logger: Logger
    token: Token
    instance: Main
    thread: threading.Thread

    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)

def startServer(instance, port, logger, token):
    with Server(("", port), Handler) as server:
        server.logger = logger
        server.token = token
        server.instance = instance
        server.allow_reuse_address = True

        try:
            server.serve_forever()
        except SystemExit:
            pass
        finally:
            server.shutdown()


def bind(port, instance, logger, token):
    thread = threading.Thread(target=startServer, args=(instance, port, logger, token))
    thread.daemon = True
    thread.start()
    logger.info("server", "Listening on 0.0.0.0:" + str(port))

