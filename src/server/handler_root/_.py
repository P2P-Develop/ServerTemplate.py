from endpoint import *


# In this example, the string specified by the text parameter will be repeated the specified number of times.

@http("GET|POST", args=(
    Argument("text", "str", "query", maximum=32,
             doc=Document(summary="Input text.")),
    Argument("count", "int", "query", minimum=1, maximum=100,
             doc=Document(summary="Multiple count."))),
      require_auth=True,
      docs=Document("Repeats the string specified with text.",
                    types="application/json",
                    responses=[
                        Response(200, doc=Document("Successful response.", example={
                            "result": "Hello, world!"
                        }))
                    ]))
def do(handler, params):
    return Response(200, params["text"] * params["count"])
