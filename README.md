<div align="center">
  <h1>ServerTemplate.py</h1>
  <p>Simple API server template and utilities for Python.</p>
</div>

## Quickstart

### Requirements

-   PyYAML

### Using ServerTemplate.py

You need to setup ServerTemplate.py.

1. Create a repository from ServerTemplate.py.
2. Start server with:
    ```bash
    $ bin/start
    ```
3. Edit config.yml:
    ```diff
    -edit: false
    +edit: true
    ```

# Caution

+ Do not uncomment `system.bind.port` in config.yml when distributing using this template.
