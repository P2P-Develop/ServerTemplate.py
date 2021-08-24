<div align="center">
  <h1>ServerTemplate.py</h1>
  <p>Simple API server template and utilities for Python.</p>
</div>

## Quickstart

### Requirements

- PyYAML

### Using ServerTemplate.py

You need to setup ServerTemplate.py.

1. Create a repository from ServerTemplate.py.
2. Start server with:
    ```bash
    $ bin/start
    ```
3. Edit `config.yml`. -> [Configuration](#Configuration)

## Configuration

- `system.bind.port` (REQUIRED) - Server listening port.


## Features

- Static routes with json or text files.
- Dynamic routes with directory tree and .py files.
  <details>
    <summary>Example</summary>
  
    ```
      /
      ├── _.py <- this is index file.
      ├── api
      │   ├── add-user.py
      │   └── get-users.py
      ├── articles
      │   └── 2021-08-25
      │       └── _.py
      └── example.py
    ```

    In this example, you can make a route of /api/add-user.
  </summary>
- Show stack trace in logs.
  <details>
    <summary>Example</summary>

  ```python
  [00:00:00 WARN] Unexpected exception while handling client request resource /example
        at server.handler.dynamic_handle(handler.py:133): handler.handle(self, path, params)
        at route._context(route.py:194): if missing(handler, params, args):
        at route.missing(route.py:43): diff = search_missing(fields, require)
  Caused by: AttributeError: 'tuple' object has no attribute 'remove'
        at route.search_missing(route.py:66): require.remove(key)
  ```

  </details>

- Argument validation with annotation.
  <details>
    <summary>Example</summary>
  
    ```python

    @route.http("GET", args=(
        ep.Argument("text", "str", "query", maximum=32),
        ep.Argument("count", "int", "query", minimum=1, maximum=100)),
    require_auth=False)
    def handle(handler, path, params):
        q = params["text"] * params["count"]
        route.success(handler, 200, q)

    ```
  </details>
- Multi-threaded routing.
- Document definition in code.
  <details>
    <summary>Example</summary>
  
    ```python
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
    ```
  
  </summary>
  
- Automatic generation of HTML documents for Swagger UI
  ```console
  $ py -3 src/gendoc.py
  ```
- Customizable commands
