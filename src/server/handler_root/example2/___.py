from endpoint import *


# Determines if the file exists and represents it as a response code.

@http("GET",
      args=Argument("path", "str", "path", maximum=128, doc=Document(summary="Input path.")),
      require_auth=True,
      docs=Document("Determines if the file exists and represents it as a response code."))
def do(handler, params):
    import os

    if os.path.exists(params["path"]):
        return SuccessResponse(code=200)
    else:
        return ErrorResponse(code=404)
