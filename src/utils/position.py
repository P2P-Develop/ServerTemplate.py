class Position:
    index: int
    line: int
    column: int
    current_char = str
    text: str

    def __init__(self, index: int, line: int, column: int, text: str):
        self.index = index
        self.line = line
        self.column = column
        self.text = text
        self.current_char = text[index]

    def advance(self):
        self.index += 1
        self.column += 1

        if self.current_char == "\n":
            self.line += 1
            self.column = 0

        return self

    def copy(self):
        return Position(self.index, self.line, self.column, self.text)
