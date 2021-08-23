import route


# In this example, the string specified by the text parameter will be repeated the specified number of times.


@route.require_args("text", "count")  # Check if the required arguments are given.
@route.validate_arg("text", "str", max_value=32)  # Check if the text is shorter than 32 characters.
@route.validate_arg("count", "int", min_value=1, max_value=100)
# Check if the count is integer and
# count is greater than 1 and less than 100
def handle(handler, path, params):
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
