import route
from server import ep


# In this example, the string specified by the text parameter will be repeated the specified number of times.


@route.http("GET", args=(
    ep.Argument("text", "str", "path", maximum=32)),
            require_auth=False)
def on_get(handler, params):
    q = params["text"]
    route.success(handler, 200, q)
