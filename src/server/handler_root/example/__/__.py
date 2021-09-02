import route


# In this example, the string specified by the text parameter will be repeated the specified number of times.


@route.http("GET", args=(
    route.Argument("text", "str", "path", maximum=32,
                   doc=route.Document(summary="Input text.")),
    route.Argument("count", "int", "path", minimum=1, maximum=100,
                   doc=route.Document(summary="Multiple count."))),
            require_auth=False,
            docs=route.Document("Repeats the string specified with text.",
                                types="application/json",
                                responses=[
                                    route.Response(200, "Successful response.", {
                                        "success": True,
                                        "result": "Hello, world!"
                                    })
                                ]))
def on_get(handler, params):
    q = params["text"] * params["count"]
    route.success(handler, 200, q)


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
