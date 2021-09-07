from traceback import format_exception
from typing import Optional, TypedDict, Dict, List, Final, Any
from dataclasses import dataclass

from levels import LogLevels, get_level_by_name
from handlers import BaseLogHandler
from record import LogRecord


@dataclass
class LoggerConfig:
    level: Optional[str]
    handlers: Optional[List[str]]


@dataclass
class LogConfig:
    handlers: Optional[Dict[str, BaseLogHandler]]
    loggers: Optional[Dict[str, LoggerConfig]]


class LoggerOptions(TypedDict):
    handlers: List[BaseLogHandler]


class Logger:
    __level: LogLevels
    __handlers: List[BaseLogHandler]

    __logger_name: Final[str]

    def __init__(self, logger_name: str, level_name: str, options: LoggerOptions):
        self.__logger_name = logger_name
        self.__level = get_level_by_name(level_name)
        self.__handlers = options["handlers"] or []

    @property
    def level(self):
        return self.__level

    @level.setter
    def level(self, level: LogLevels):
        self.__level = level

    @property
    def level_name(self):
        return self.__level.name

    @level_name.setter
    def level_name(self, level_name: str):
        self.__level = get_level_by_name(level_name)

    @property
    def logger_name(self):
        return self.__logger_name

    @property
    def handlers(self) -> List[BaseLogHandler]:
        return self.__handlers

    @handlers.setter
    def handlers(self, handlers: List[BaseLogHandler]):
        self.__handlers = handlers

    @staticmethod
    def as_string(data: Any):
        if type(data) is str:
            return data
        elif data is None or type(data) is int or type(data) is float or type(data) is bool:
            return str(data)
        elif type(data) is Exception or issubclass(Exception, type(data)):
            return format_exception(type(data), data, data.__traceback__)
        else:
            return repr(data)

    def debug(self, *args):
        return self.__log(LogLevels.Debug, *args)

    def hint(self, *args):
        return self.__log(LogLevels.Hint, *args)

    def info(self, *args):
        return self.__log(LogLevels.Info, *args)

    def warning(self, *args):
        return self.__log(LogLevels.Warning, *args)

    def error(self, *args):
        return self.__log(LogLevels.Error, *args)

    def fatal(self, *args):
        return self.__log(LogLevels.Fatal, *args)

    def __log(self, level: LogLevels, message: Any, *args):
        if self.level > level:
            return callable(message) and None or message

        fn_result: Optional[Any]
        log_message: str

        if callable(message):
            fn_result = message()
            log_message = self.as_string(fn_result)
        else:
            log_message = self.as_string(message)

        record = LogRecord(log_message, list(args), level, self.logger_name)

        for handler in self.__handlers:
            handler.handle(record)

        return callable(message) and fn_result or message
