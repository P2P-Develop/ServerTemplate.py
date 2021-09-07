from typing import List

from utils.position import Position


class FormattingException(Exception):
    start_position: Position
    end_position: Position
    text: str

    def __init__(self, message: str, start_position: Position, end_position: Position, text: str):
        super(message)

        self.start_position = start_position
        self.position = end_position
        self.text = text

    def print_position(self):
        result = ""

        index_start = max(self.text.rfind("\n", 0, self.start_position.index), 0)
        index_end = self.text.find("\n", index_start + 1)

        if index_end < 0:
            index_end = len(self.text)

        line_count = self.end_position.line - self.start_position.line + 1

        for i in range(line_count):
            line = self.text[index_start:index_end]
            column_start = self.start_position.column if i == 0 else 0
            column_end = self.end_position if i == line_count - 1 else len(line) - 1

            result += line + "\n"
            result += " " * column_start

            point_count = column_end - column_start
            point_literal = "^" if point_count <= 1 else "~"

            result += point_literal * point_count

            index_start = index_end
            index_end = self.text.find("\n", index_start + 1)

            if index_end < 0:
                index_end = len(self.text)

        return result.replace("\t", "")


class ExpectedFormatException(FormattingException):
    expected_characters: List[str]

    def __init__(self, expected_characters: List[str], start_position: Position, end_position: Position, text: str):
        result = ""

        characters_length = len(expected_characters)

        for i, char in enumerate(expected_characters):
            if characters_length == 1:
                result += "'{}'".format(char)
            else:
                if i == characters_length - 1:
                    result += "or '{}'".format(char)
                elif i != characters_length - 2:
                    result += "'{}',".format(char)
                else:
                    result += "'{}'".format(char)

            if i != characters_length - 1:
                result += " "

        super().__init__("Expected Character " + result, start_position, end_position, text)


class UnknownCharException(FormattingException):
    def __init__(self, unknown_character: str, start_position: Position, end_position: Position, text: str):
        super().__init__("Unknown Character " + unknown_character, start_position, end_position, text)
