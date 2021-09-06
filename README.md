<div align="center">
  <h1>ServerTemplate.py</h1>
  <p>Simple API server template and utilities for Python.</p>
</div>

## Quickstart

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/ebbfeaab7736420c9ff81aa1bf73a2bc)](https://app.codacy.com/gh/P2P-Develop/ServerTemplate.py?utm_source=github.com&utm_medium=referral&utm_content=P2P-Develop/ServerTemplate.py&utm_campaign=Badge_Grade_Settings)

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
- RESTful api support
  <details>
    <summary>Example</summary>

  ```python
  # /user/__.py
  @http("GET", args=(Argument("user_id", "string", "path")))
  def handle(handler, params):
      pass
  
  @http("PUT|DELETE", args=(Argument("user_id", "string", "path"), 
                            Argument("user_name", "string", "query"),
                            Argument("data", "int", "body")))
  def handle(handler, params):
      pass
  ```
  </details>
- Show stack trace in logs.
  <details>
    <summary>Example</summary>

  ```python
  [00:00:00 WARN] Unexpected exception while handling client request resource /example
        at server.handler.dynamic_handle(handler.py:133): handler.handle(self, path, params)
        at _context(py:194): if missing(handler, params, args):
        at missing(py:43): diff = search_missing(fields, require)
  Caused by: AttributeError: 'tuple' object has no attribute 'remove'
        at search_missing(py:66): require.remove(key)
  ```

  </details>

- Argument validation with annotation.
  <details>
    <summary>Example</summary>

    ```python
        
    from endpoint import *
    impport route 
    @http("GET", args=(
        Argument("text", "str", "query", maximum=32),
        Argument("count", "int", "query", minimum=1, maximum=100)),
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
        from endpoint import *
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
    ```
  
  </details>
  
- Automatic generation of HTML documents for Swagger UI
  ```console
  $ py -3 src/gendoc.py
  ```
- Customizable commands
