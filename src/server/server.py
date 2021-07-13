from socketserver import ThreadingTCPServer
from server.handler import Handler
import socket
from ssl import wrap_socket
import threading


class Server(ThreadingTCPServer, object):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)


def startServer(instance, port, logger, token):
    server = Server(("", port), Handler)
    server.logger = logger
    server.token = token
    server.instance = instance
    server.serve_forever()


def bind(port, instance, logger, token):
    t = threading.Thread(target=startServer, args=(
        instance, port, logger,  token))
    t.start()
    logger.info("server", "Listening on 0.0.0.0:" + str(port))
