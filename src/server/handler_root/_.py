from utils import result


def handle(handler, path, params):
    if "text" in params:
        q = params["text"]
    else:
        q = "Hello, world!"
    result.success(handler, 200, q)


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
