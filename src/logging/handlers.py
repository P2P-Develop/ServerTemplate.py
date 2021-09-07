from typing import Optional, Union, Callable, List, Dict
from datetime import datetime

from levels import LogLevels, get_level_by_name
from record import LogRecord

from formatting import ExpectedFormatException, UnknownCharException

from utils.position import Position
from utils.colors import supports_color


def current_log_time(date: datetime):
    return date.isoformat(" ")


Formatter = Optional[Union[str, Callable[[], str]]]


class BaseLogHandler:
    level: LogLevels
    level_name: str
    formatter: Formatter
    position = Optional[Position]

    def __init__(self, level_name: str, formatter: Formatter):
        self.level = get_level_by_name(level_name)
        self.level_name = level_name

        if formatter:
            self.formatter = formatter
        else:
            self.formatter = "[ %f{:<7}($U(%l)) ] %d{Y-m-d H:M:S} (%n) - %m"

    def handle(self, log_record: LogRecord):
        if self.level > log_record.level:
            return

        return self.log(self.format(log_record), log_record.level)

    def validate_format(self):
        pass

    def format(self, log_record: LogRecord) -> str:
        if callable(self.formatter):
            return self.formatter(log_record).format()

        result = ""

        self.position = Position(0, 0, 0, self.formatter)

        def dummy_fn(text: str, *args, **kwargs):
            return text

        def loop():
            if self.position.current_char == "%":
                return make_format_char()
            else:
                self.position.advance()

                return self.position.current_char

        def format_inside_bracket(bracket_start_char="{", bracket_end_char="}",
                                  format_fn: Callable[[str, ...], str] = None,
                                  *args, **kwargs):
            if format_fn is None:
                format_fn = dummy_fn

            start_position = self.position.copy()

            self.position.advance()

            if self.position.current_char != bracket_start_char:
                raise ExpectedFormatException([bracket_start_char], start_position, self.position, self.formatter)

            characters = ""

            while self.position.current_char != bracket_end_char:
                if self.position.current_char is None:
                    raise ExpectedFormatException([bracket_end_char], start_position, start_position, self.formatter)
                elif self.position.current_char == "%":
                    characters += make_format_char()

                characters += self.position.current_char

                self.position.advance()

            return format_fn(characters, *args, **kwargs)

        def make_format_char():
            start_position = self.position.copy()

            self.position.advance()

            if self.position.current_char == "%":
                return "%"
            elif self.position.current_char == "U":
                return format_inside_bracket(format_fn=str.upper)
            elif self.position.current_char == "u":
                return format_inside_bracket(format_fn=str.lower)
            elif self.position.current_char == "c":
                return format_inside_bracket(format_fn=str.capitalize)
            elif self.position.current_char == "l":
                return log_record.level_name
            elif self.position.current_char == "L":
                return str(log_record.level)
            elif self.position.current_char == "d":
                def add_datetime_prefix(text: str):
                    datetime_result = ""

                    for char in text:
                        if char in "aAwdbBmyYHIpMSfzZjUWcxX%GuV":
                            datetime_result += "%" + char
                        else:
                            datetime_result += char

                    return log_record.date.strftime(datetime_result)

                return format_inside_bracket(format_fn=add_datetime_prefix)
            elif self.position.current_char == "n":
                return log_record.logger_name
            elif self.position.current_char == "f":
                format_character = format_inside_bracket()
                format_args: List[str] = []

                while self.position.current_char != "(":
                    format_start_position = self.position.copy()
                    format_arg = ""

                    while self.position.current_char != ")":
                        if self.position.current_char is None:
                            raise ExpectedFormatException([")"], format_start_position, format_start_position,
                                                          self.formatter)

                        format_arg += loop()

                    format_args.append(format_arg)

                return format_character.format(*format_args)
            elif self.position.current_char == "m":
                return log_record.message
            elif self.position.current_char in "xX":
                color_codes = format_inside_bracket().split(",")

                if len(color_codes) < 1:
                    raise ExpectedFormatException(["digits", ","], start_position, start_position, self.formatter)

                font_styles: Optional[List[int]] = None
                font_styles_map = ["bold", "dim", "faint", "italic", "underline", "blink", "inverse", "reverse", "hidden", "invisible", "strikethrough"]
                fg_color: Optional[int] = None
                bg_color: Optional[int] = None

                for code in map(color_code.lower() for color_code in color_codes):
                    if code.isdigit():
                        parsed_code = int(code)
                        if fg_color is None:
                            fg_color = parsed_code
                        elif bg_color is None:
                            bg_color = parsed_code
                    elif code in font_styles_map:
                        font_styles.append(({
                            "bold": 1,
                            "dim": 2,
                            "faint": 2,
                            "italic": 3,
                            "underline": 4,
                            "blink": 5,
                            "inverse": 7,
                            "reverse": 7,
                            "hidden": 8,
                            "invisible": 8,
                            "strikethrough": 9
                        })[code])
                    elif code in map("bg-" + font_style for font_style in font_styles_map):
                        font_styles.append(({
                            "bg-bold": 22,
                            "bg-dim": 22,
                            "bg-faint": 22,
                            "bg-italic": 23,
                            "bg-underline": 24,
                            "bg-blink": 25,
                            "bg-inverse": 27,
                            "bg-reverse": 27,
                            "bg-hidden": 28,
                            "bg-invisible": 28,
                            "bg-strikethrough": 29
                        })[code])

                wrap_text = "" if self.formatter[self.position.index + 1] != "{" else format_inside_bracket()
                is_wrap_empty = wrap_text == ""

                if type(self).__name__ != "ConsoleLogHandler" or not supports_color():
                    return "" if is_wrap_empty else wrap_text

                esc = "\033["
                reset = esc + "0m"

                made_ansi = esc

                for i, font_style in enumerate(font_styles):
                    if i == len(font_styles) - 1:
                        made_ansi += str(font_style) + "m"
                    else:
                        made_ansi += str(font_style) + "m" + esc

                if self.position.current_char == "x":
                    made_ansi += str(int(fg_color) + 30)

                    if bg_color is not None:
                        made_ansi += ";" + str(bg_color + 40) + "m"
                else:
                    made_ansi += "38;5;" + str(fg_color) + "m" if fg_color is not None and fg_color != "" else ""
                    made_ansi += esc + "48;5;" + str(bg_color) + "m" if bg_color is not None else ""

                if is_wrap_empty:
                    return made_ansi + ";"

                return made_ansi + ";" + wrap_text + reset
            elif self.position.current_char == "#":
                convert_fn = getattr(self, "convert_fn", None)

                if callable(convert_fn):
                    return format_inside_bracket(format_fn=convert_fn)

                return format_inside_bracket()
            else:
                raise UnknownCharException("after %", start_position, self.position, self.formatter)

        while self.position.current_char is not None:
            result += loop()

        return result


class ConsoleLogHandler(BaseLogHandler):

