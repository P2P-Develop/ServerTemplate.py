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
  </details>
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

import route    @route.http("GET", args=(
        route.Argument("text", "str", "query", maximum=32),
        route.Argument("count", "int", "query", minimum=1, maximum=100)),
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
    ```
  
  </details>
  
- Automatic generation of HTML documents for Swagger UI
  ```console
  $ py -3 src/gendoc.py
  ```
- Customizable commands
