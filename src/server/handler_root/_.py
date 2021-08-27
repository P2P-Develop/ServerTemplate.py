import route

# In this example, the string specified by the text parameter will be repeated the specified number of times.


@route.http("GET", args=(
    route.Argument("text", "str", "query", maximum=32),
    route.Argument("count", "int", "query", minimum=1, maximum=100)),
            require_auth=False)
def on_get(handler, params):
    q = params["text"] * params["count"]
    route.success(handler, 200, q)


@route.http("POST", args=(
    route.Argument("text", "str", "body", maximum=32),
    route.Argument("count", "int", "body", minimum=1, maximum=100)))
def on_post(handler, params):
    q = params["text"] * params["count"]
    route.success(handler, 200, q)


def params():
    return [
        {
            "name": "text",
            "in": "query",
            "about": "Input text.",
            "required": True,
            "type": "string"
        },
        {
            "name": "count",
            "in": "query",
            "about": "Count.",
            "required": True,
            "type": "integer",
            "minimum": 1,
            "maximum": 100
        }
    ]


def docs():
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
