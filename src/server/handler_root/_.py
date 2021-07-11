from utils import result


def handle(handler, path, params):
    result.success(handler, 200, "Hello, World!")
