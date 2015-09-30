import logging
import string
import tokens
from .. import exceptions


class Lexer(object):

    def __init__(self, src):
        self.src = src
        self.char_pos = 0
        self.current_token = None
        self.tokens = []
        self.in_escape = False
        self.in_line_comment = False
        self.in_block_comment = False
        self.line_num = 1

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
            raise exceptions.EndOfFileException()

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
                logging.debug(
                    "[In token: %s] Character is %s" %
                    (self.current_token, char))
            except exceptions.EndOfFileException:
                if self.current_token is not None:
                    self.push_token()
                return self.tokens

            if self.current_token is None:
                # No current state
                if char == '\n' and not self.in_block_comment:
                    self.in_line_comment = False
                    self.tokens.append(
                        tokens.LineTerminatorToken(self.line_num))
                    self.line_num += 1
                    logging.debug(
                        'Lexer increments line to %d' % self.line_num)
                elif char == '*' and self.next_char == '/':
                    if not self.in_block_comment:
                        raise exceptions.ParseError(
                            "Ending block comment token unexpected.")
                    self.in_block_comment = False
                    self.skip_ahead()
                elif self.in_line_comment or self.in_block_comment:
                    # ignore whatever is here, but
                    # increment line counter if needed
                    if char == '\n':
                        logging.debug(
                            "Lexer increments line to %d" % self.line_num)
                        self.line_num += 1
                    continue
                elif char in "'\"":
                    self.current_token = tokens.StringLiteralToken(
                        self.line_num, '', delimiter=char)
                elif char in string.digits or char == '.' and \
                        self.next_char in string.digits:
                    self.current_token = tokens.NumberLiteralToken(
                        self.line_num, char)
                elif char in string.letters or char == '_':
                    self.current_token = tokens.IdentifierToken(
                        self.line_num, char)
                elif char == '>':
                    if self.next_char == '=':
                        self.save_token(tokens.GreaterThanEqualOperatorToken(
                            self.line_num))
                        self.skip_ahead()
                    else:
                        self.save_token(tokens.GreaterThanOperatorToken(
                            self.line_num))
                elif char == '<':
                    if self.next_char == '=':
                        self.save_token(tokens.LessThanEqualOperatorToken(
                            self.line_num))
                        self.skip_ahead()
                    else:
                        self.save_token(tokens.LessThanOperatorToken(
                            self.line_num))
                elif char == '=':
                    if self.next_char == '=':
                        # comparison, not assignment
                        self.save_token(tokens.ComparisonOperatorToken(
                            self.line_num))
                        self.skip_ahead()
                    else:
                        self.save_token(tokens.AssignmentOperatorToken(
                            self.line_num))
                elif char == '+':
                    self.save_token(tokens.AdditionOperatorToken(
                        self.line_num))
                elif char == '-':
                    self.save_token(tokens.SubtractionOperatorToken(
                        self.line_num))
                elif char == '/' and self.next_char == '/':
                    # comment!
                    self.in_line_comment = True
                    self.skip_ahead()
                elif char == '/' and self.next_char == '*':
                    self.in_block_comment = True
                    self.skip_ahead()
                elif char == '/':
                    self.save_token(tokens.DivisionOperatorToken(
                        self.line_num))
                elif char == '*':
                    if self.next_char == '*':
                        self.save_token(tokens.ExponentOperatorToken(
                            self.line_num))
                        self.skip_ahead()
                    else:
                        self.save_token(tokens.MultiplicationOperatorToken(
                            self.line_num))
                elif char == '\\' and self.next_char == '\n':
                    # escaped line terminator
                    self.skip_ahead()

                elif char == '(':
                    self.save_token(tokens.LeftParenToken(self.line_num))
                elif char == ')':
                    self.save_token(tokens.RightParenToken(self.line_num))
                elif char == '{':
                    self.save_token(tokens.LeftCurlyBraceToken(self.line_num))
                elif char == '}':
                    self.save_token(tokens.RightCurlyBraceToken(self.line_num))
                elif char == '[':
                    self.save_token(tokens.LeftSquareBraceToken(self.line_num))
                elif char == ']':
                    self.save_token(tokens.RightSquareBraceToken(
                        self.line_num))
                elif char == ':':
                    self.save_token(tokens.ColonToken(self.line_num))
                elif char == ',':
                    self.save_token(tokens.CommaToken(self.line_num))
                elif char in string.whitespace:
                    pass
                else:
                    raise exceptions.UnexpectedCharacter(self.line_num, char)
            elif isinstance(self.current_token, tokens.StringLiteralToken):
                if self.in_escape:
                    self.current_token.body += char
                    self.in_escape = False
                elif char == '/':
                    self.in_escape = True
                elif char == self.current_token.delimiter:
                    self.push_token()
                else:
                    self.push_char(char)

            elif isinstance(self.current_token, tokens.NumberLiteralToken):
                if char in string.digits or char == '.':
                    if '.' in self.current_token.body:
                        raise exceptions.ParseError("Second . found in number")
                    self.push_char(char)
                else:
                    self.push_token()
                    self.back_up()

            elif isinstance(self.current_token, tokens.IdentifierToken):
                if char in string.digits or char in \
                        string.letters or char in '$_':
                    self.push_char(char)
                elif char == '.':
                    # object attribute resolution operator
                    self.push_token()
                    self.save_token(
                        tokens.DotNotationOperatorToken(self.line_num))
                else:
                    self.push_token()
                    self.back_up()

        # End it all
        if not isinstance(self.tokens[-1], tokens.LineTerminatorToken):
            self.line_num += 1
            self.tokens.append(tokens.LineTerminatorToken(self.line_num))
