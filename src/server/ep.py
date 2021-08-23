import pathlib
import importlib


class Argument:
    _types = ["string", "boolean", "number", "enum", "other"]

    def __init__(self,
                 type: str,
                 required: bool,
                 description: str = None,
                 min: int = None,
                 max: int = None):
        self.type = type
        self.required = required,
        self.description = description,
        self.min = min
        self.max = max


class EndPoint:
    def __init__(self,
                 absolute_path: str,
                 handler,
                 method,
                 no_auth: bool = False,
                 require_args: list = None):
        self.absolute_path = absolute_path
        self.handler = handler,
        self.no_auth = no_auth
        self.require_args = require_args if require_args is None else []

global loader

class Loader:
    def __init__(self):
        self.endpoints = {}
        self.signals = []

    def load(self):
        for file in pathlib.Path("src/server/handler_root/").glob("**/*.py"):
            try:
                moduleName = ".".join(file.parts)[4:-3]
                importlib.import_module(moduleName)
            except Exception as e:
                pass
        self._makecache()

    def _makecache(self):
        for s in self.signals:
            module = s["mod"]
            method = s["method"]
            function = s["func"]
            require_args = s["require_args"]
            no_auth = s["no_auth"]


