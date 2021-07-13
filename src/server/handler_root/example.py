from utils import result

# /example


def handle(handler, path, params):
    result.success(handler, 200, "It's working!")
