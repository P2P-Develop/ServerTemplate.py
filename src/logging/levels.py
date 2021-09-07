from enum import IntEnum, unique


@unique
class LogLevels(IntEnum):
    Debug = 0,
    Hint = 10,
    Info = 20,
    Warning = 30,
    Error = 40,
    Fatal = 50


def get_level_by_name(level_name: str) -> LogLevels:
    if level_name not in LogLevels.__members__.items():
        raise KeyError()

    return LogLevels[level_name]
