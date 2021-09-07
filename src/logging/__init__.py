from typing import Optional, List

from logging.logger import Logger, LogConfig, LoggerConfig
from handlers import BaseLogHandler

DEFAULT_LEVEL = "Info"
DEFAULT_CONFIG: LogConfig = LogConfig({
    "default": [
        {
            "name": "console",
            "level": DEFAULT_LEVEL
        }
    ]
}, {
    "default": LoggerConfig(DEFAULT_LEVEL, ["default"])
})

state = {
    "handlers": {},
    "loggers": {},
    "config": DEFAULT_CONFIG
}


def get_logger(name: Optional[str] = None) -> Logger:
    global state

    if name is None:
        d = state["loggers"].get("default")

        if d is None:
            raise Exception('"default" logger must be set for getting logger without name')

    result = state["loggers"].get(name)

    if not result:
        new_logger = Logger(name, DEFAULT_LEVEL, DEFAULT_CONFIG)

        state["loggers"][name] = new_logger

        return new_logger

    return result


def setup(config: LogConfig):
    global state

    state["config"] = {
        "handlers": {*DEFAULT_CONFIG["handlers"], *config["handlers"]},
        "loggers": {*DEFAULT_CONFIG["loggers"], *config["loggers"]}
    }

    for handler in state["handlers"]:
        handler.destroy()

    state["handlers"].clear()

    handlers = state["config"]["handlers"] or {}

    for handler_name in handlers:
        state["handlers"][handler_name] = handlers["handler_name"]

    loggers = state["config"]["logging"] or {}

    for logger_name in loggers:
        logger_config = loggers[logger_name]
        handler_names = logger_config.handlers or {}
        handlers: List[BaseLogHandler] = {}

        for handler_name in handler_names:
            handler = state["handlers"].get(handler_name)

            if handler is not None:
                handlers.append(handler)

    level_name = logger_config.level if logger_config is not None else DEFAULT_LEVEL
    new_logger = Logger(logger_name, level_name, {"handlers": handlers})

    state["loggers"][logger_name] = new_logger


setup(DEFAULT_CONFIG)
