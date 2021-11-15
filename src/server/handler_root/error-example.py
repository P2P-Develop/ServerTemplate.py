from endpoint import *


@http("*",
      require_auth=False,
      docs=Document("Always an error."))
def do(handler, params):
    method_chain(0)
    return SuccessResponse(200)


def method_chain(count):
    if count < 10:
        method_chain(count + 1)
    else:
        method_chain_end()


def method_chain_end():
    raise RecursionError("This is an example error.")
