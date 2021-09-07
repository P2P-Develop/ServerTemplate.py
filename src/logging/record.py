from typing import List, Final
from datetime import datetime

from levels import LogLevels


class LogRecord:
    message: Final[str]
    args: Final[List[str]]
    level: Final[int]
    logger_name: Final[str]

    date: datetime

    def __init__(self, message: str, args: List[str], level: int, logger_name: str):
        self.message = message
        self.args = args
        self.level = level
        self.logger_name = logger_name

        self.date: datetime = datetime.now()

        self.level_name = LogLevels(level).name
