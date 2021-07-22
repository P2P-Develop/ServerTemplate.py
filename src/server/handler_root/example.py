from utils import result


# /example


def handle(handler, path, params):
    result.success(handler, 200, "It's working!")


def genDoc():
    return {
        "get": {
            "about": "Example document.",
            "returns": "text/plain",           # Return mime type.
            200: {                             # HTTP Code
                "about": "Example response.",
                "example": "It works!"         # Objects, texts, numbers, and boolean values can be set.
            }
        }
    }
