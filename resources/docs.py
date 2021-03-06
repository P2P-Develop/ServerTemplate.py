import os

from endpoint import *
import route


@http("GET", require_auth=False,
      docs=Document("View document.",
                    types="text/html",
                    responses=[
                        Response(200, "Successful response.")
                    ]))
def on_get(handler, params):
    if not os.path.exists("docs.html"):
        route.post_error(handler, route.Cause.RESOURCE_NOTFOUND)
        return
    with open("docs.html", "r", encoding="utf-8") as r:
        route.write(handler, 200, r.read(), "text/html")
