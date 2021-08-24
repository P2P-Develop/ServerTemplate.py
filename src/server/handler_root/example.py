import route


# /example


def handle(handler, params):
    route.success(handler, 200, "It's working!")


def docs():
    return {
        "get": {
            "about": "Example document.",
            "returns": "text/plain",  # Return mime type.
            200: {  # HTTP Code
                "about": "Example response.",
                "example": "It works!"  # Objects, texts, numbers, and boolean values can be set.
            }
        }
    }
