from typing import Optional

from logging.formatter import Position


class LogFormatLexer:
    text: str
    position: Position
    current_char: Optional[str]

    def __init__(self, text: str):
        self.text = text
        self.position = Position(-1, 0, -1, text)
        self.current_char = None

        self.advance()

    def advance(self):
        self.position.advance(self.current_char)
        self.current_char = self.text[self.pos.index] if self.pos.index < len(self.text) else None

    def make_tok
