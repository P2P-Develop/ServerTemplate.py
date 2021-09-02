from endpoint import *
import route


# In this example, the string specified by the text parameter will be repeated the specified number of times.


@http("GET", args=(
    Argument("text", "str", "path", maximum=32,
             doc=Document(summary="Input text.")),
    Argument("count", "int", "path", minimum=1, maximum=100,
             doc=Document(summary="Multiple count."))),
      require_auth=False,
      docs=Document("Repeats the string specified with text.",
                    types="application/json",
                    responses=[
                        Response(200, "Successful response.", {
                            "success": True,
                            "result": "Hello, world!"
                        })
                    ]))
def on_get(handler, params):
    q = params["text"] * params["count"]
    route.success(handler, 200, q)
