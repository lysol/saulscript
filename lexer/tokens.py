class Token(object):

    def append(self, txt):
        self.body += txt

    def show(self):
        return self.body

    def __init__(self, body):
        self.body = body

    def __str__(self):
        return self.body

    def __repr__(self):
        return self.__str__()


class LineTerminatorToken(Token):

    def __init__(self):
        super(LineTerminatorToken, self).__init__("\n")


class BinaryOperatorToken(Token):

    def __init__(self, precedence, body):
        self.precedence = precedence
        super(BinaryOperatorToken, self).__init__(body)


class IdentifierToken(Token):

    def __init__(self, body):
        super(IdentifierToken, self).__init__(body)


class LiteralToken(Token):
    pass


class NumberLiteralToken(LiteralToken):

    def __init__(self, body=''):
        super(NumberLiteralToken, self).__init__(body)


class StringLiteralToken(LiteralToken):

    def __init__(self, body, delimiter="'"):
        self.delimiter = delimiter
        super(StringLiteralToken, self).__init__(body)

    def show(self):
        return '"%s"' % (self.body.replace('"', '\\"'))


class AssignmentOperatorToken(BinaryOperatorToken):

    def __init__(self):
        super(AssignmentOperatorToken, self).__init__(14, '=')


class ComparisonOperatorToken(BinaryOperatorToken):

    def __init__(self):
        super(ComparisonOperatorToken, self).__init__(7, '==')


class AdditionOperatorToken(BinaryOperatorToken):

    def __init__(self):
        super(AdditionOperatorToken, self).__init__(4, '+')


class SubtractionOperatorToken(BinaryOperatorToken):

    def __init__(self):
        super(SubtractionOperatorToken, self).__init__(4, '-')


class DivisionOperatorToken(BinaryOperatorToken):

    def __init__(self):
        super(DivisionOperatorToken, self).__init__(3, '/')


class MultiplicationOperatorToken(BinaryOperatorToken):

    def __init__(self):
        super(MultiplicationOperatorToken, self).__init__(3, '*')


class ExponentOperatorToken(BinaryOperatorToken):

    def __init__(self):
        super(ExponentOperatorToken, self).__init__(2, '**')


class GreaterThanOperatorToken(BinaryOperatorToken):

    def __init__(self):
        super(GreaterThanOperatorToken, self).__init__(6, '>')


class LessThanOperatorToken(BinaryOperatorToken):

    def __init__(self):
        super(LessThanOperatorToken, self).__init__(6, '<')


class GreaterThanEqualOperatorToken(BinaryOperatorToken):

    def __init__(self):
        super(GreaterThanEqualOperatorToken, self).__init__(6, '>=')


class LessThanEqualOperatorToken(BinaryOperatorToken):

    def __init__(self):
        super(LessThanEqualOperatorToken, self).__init__(6, '<=')


class DotNotationOperatorToken(BinaryOperatorToken):

    def __init__(self):
        super(DotNotationOperatorToken, self).__init__(1, '.')


class LeftParenToken(BinaryOperatorToken):

    def __init__(self):
        super(LeftParenToken, self).__init__(1, '(')


class RightParenToken(BinaryOperatorToken):

    def __init__(self):
        super(RightParenToken, self).__init__(9, ')')
