<div align="center">
  <h1>ServerTemplate.py</h1>
  <p>Simple API server template and utilities for Python.</p>
  <a href="https://github.com/P2P-Develop/ServerTemplate.py/blob/main/LICENSE">
    <img alt="GitHub license" src="https://img.shields.io/github/license/P2P-Develop/ServerTemplate.py?style=flag-square">
  </a>
  <a href="https://www.codacy.com/gh/P2P-Develop/ServerTemplate.py/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=P2P-Develop/ServerTemplate.py&amp;utm_campaign=Badge_Grade">
    <img alt="Codacy grade" src="https://img.shields.io/codacy/grade/91a6fa96fccf431c8c89fa2181dce966?style=flat-square">
  </a>
  <a href="https://github.com/P2P-Develop/ServerTemplate.py/commits">
    <img alt="GitHub commit activity" src="https://img.shields.io/github/commit-activity/m/P2P-Develop/ServerTemplate.py?style=flat-square">  
  </a>
  <a href="https://www.python.org/downloads/">
    <img alt="Supported versions" src="https://img.shields.io/badge/python-3.7%7C3.8%7C3.9-%234584b6?style=flat-square">
  </a>
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
- `system.request.header_readlimit` - Bytes maximum read per line.
- `system.request.default_protocol` - Default protocol.
- `system.request.header_limit` - Limit of headers clients can be send.
- `system.request.default_content_type` - Default type if content type does not match.
- `system.route_paths` - Endpoint root directory.


## Features

- Static routes with json or text files.
- Dynamic routes with directory tree and .py files.
  <details>
    <summary>Example</summary>
  
    ```
      /
      ├── _.py <- this is index file.
      ├── api
      │   ├── user.py
      │   └── post.py
      ├── articles
      │   ├── a.py
      │   └── __.py
      ├── download
      │   └── ___.py
      ├── video
      │   └── __
      │    ├── watch.py
      │    └── info.py
      └── example.py
    ```

    In this example, you can make a route of `/api/user`.  
    Also, you can make a route of `/download/path/to/foo.bar` and you can make a route of `/articles/foobar`.  
    `__` supports only one path component and can be used multiple times, but cannot contain `/`.
    You can also use `__` for directories.  
    `___.py` cannot be used more than once, but it can contain `/`. The directory where `___.py` is placed cannot contain any other files.
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
  
  @http(Method.PATCH & Method.HEAD, args=(Argument("user_id", "string", "path"))
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
