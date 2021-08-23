import route


@route.require_args("text")  # Check if the required arguments are given.
def handle(handler, path, params):
    q = params["text"]
    route.success(handler, 200, q)


def params():
    return [
        {
            "name": "text",
            "in": "query",
            "about": "Input text.",
            "required": True,
            "type": "string"
        }
    ]


def genDoc():
    return {
        "get": {
            "about": "Outputs the specified text.",
            "returns": "application/json",
            200: {
                "about": "Successful response.",
                "example": {
                    "success": True,
                    "result": "Hello, world!"
                }
            }
        }
    }
