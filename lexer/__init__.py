import string
from tokens import *


class EndOfFileException(Exception):
    pass


class ParseError(Exception):

    def __init__(self, message):
        self.message = message


class Lexer(object):

    def __init__(self, src):
        self.src = src
        self.char_pos = 0
        self.current_token = None
        self.tokens = []
        self.in_escape = False

    @property
    def next_char(self):
        try:
            return self.src[self.char_pos]
        except IndexError:
            return None

    def get_char(self):
        try:
            char = self.src[self.char_pos]
            self.skip_ahead()
            return char
        except IndexError:
            raise EndOfFileException()

    def back_up(self):
        self.char_pos -= 1

    def skip_ahead(self):
        self.char_pos += 1

    def save_token(self, token):
        self.tokens.append(token)

    def push_token(self):
        self.save_token(self.current_token)
        self.current_token = None

    def push_char(self, char):
        self.current_token.body += char

    def run(self):

        while True:
            try:
                char = self.get_char()
            except EndOfFileException:
                if self.current_token is not None:
                    self.push_token()
                return self.tokens

            if self.current_token is None:
                # No current state
                if char in "'\"":
                    self.current_token = StringLiteralToken(char)
                elif char in string.digits or char == '.' or char == '-' and \
                        self.next_char in string.digits:
                    self.current_token = NumberLiteralToken(char)
                elif char in string.letters:
                    self.current_token = IdentifierToken(char)
                elif char == '>':
                    if self.next_char == '=':
                        self.save_token(GreaterThanEqualOperatorToken())
                        self.skip_ahead()
                    else:
                        self.save_token(GreaterThanOperatorToken())
                elif char == '<':
                    if self.next_char == '=':
                        self.save_token(LessThanEqualOperatorToken())
                        self.skip_ahead()
                    else:
                        self.save_token(LessThanOperatorToken())
                elif char == '=':
                    if self.next_char == '=':
                        # comparison, not assignment
                        self.save_token(ComparisonOperatorToken())
                        self.skip_ahead()
                    else:
                        self.save_token(AssignmentOperatorToken())
                elif char == '+':
                    self.save_token(AdditionOperatorToken())
                elif char == '-':
                    self.save_token(SubtractionOperatorToken())
                elif char == '/':
                    self.save_token(DivisionOperatorToken())
                elif char == '*':
                    if self.next_char == '*':
                        self.save_token(ExponentOperatorToken())
                        self.skip_ahead()
                    else:
                        self.save_token(MultiplicationOperatorToken())
                elif char == '\\' and self.next_char == '\n':
                    # escaped line terminator
                    self.skip_ahead()
                elif char == '\n':
                    self.tokens.append(LineTerminatorToken())
                elif char == '(':
                    self.save_token(LeftParenToken())
                elif char == ')':
                    self.save_token(RightParenToken())
                elif char in string.whitespace:
                    pass

            elif isinstance(self.current_token, StringLiteralToken):
                if self.in_escape:
                    self.current_token.body += char
                    self.in_escape = False
                elif char == '/':
                    self.in_escape = True
                elif char == self.current_token.delimiter:
                    self.push_token()
                else:
                    self.push_char(char)

            elif isinstance(self.current_token, NumberLiteralToken):
                if char in string.digits or char == '.':
                    if '.' in self.current_token.body:
                        raise ParseError("Second . found in number")
                    self.push_char(char)
                else:
                    self.push_token()
                    self.back_up()

            elif isinstance(self.current_token, IdentifierToken):
                if char in string.digits or char in string.letters:
                    self.push_char(char)
                elif char == '.':
                    # object attribute resolution operator
                    self.push_token()
                    self.save_token(DotNotationOperatorToken())
                else:
                    self.push_token()
                    self.back_up()
