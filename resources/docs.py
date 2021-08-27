import os
import route


@route.http("GET", require_auth=False)
def on_get(handler, params):
    if not os.path.exists("docs.html"):
        route.post_error(handler, route.Cause.RESOURCE_NOTFOUND)
        return
    with open("docs.html", "r", encoding="utf-8") as r:
        route.write(handler, 200, r.read(), "text/html")
