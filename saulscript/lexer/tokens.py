from ..syntax_tree import nodes


class Token(object):

    def append(self, txt):
        self.body += txt

    def show(self):
        return self.body

    def __init__(self, line_num, body):
        self.body = body
        self.line_num = line_num

    def __str__(self):
        return self.body

    def __repr__(self):
        return self.__str__()

    def get_node(self, line_num):
        # ha ha this is bad
        return self


class LineTerminatorToken(Token):

    def __init__(self, line_num):
        super(LineTerminatorToken, self).__init__(line_num, "\n")


class OperatorToken(Token):

    LEFT = 0
    RIGHT = 1

    def get_node(self, line_num):
        raise NotImplementedError(
            "Please define a type of node for this token to return")

    def __init__(self, line_num, precedence, body, associativity=None, unary=False):
        self.precedence = precedence
        self.associativity = associativity \
            if associativity is not None else self.LEFT
        super(OperatorToken, self).__init__(line_num, body)
        self.unary = unary


class BinaryOperatorToken(OperatorToken):
    pass


class UnaryOperatorToken(OperatorToken):
    pass


class IdentifierToken(Token):

    def __init__(self, line_num, body):
        super(IdentifierToken, self).__init__(line_num, body)

    def __repr__(self):
        return "<Identifier: %s>" % self.body

    def __str__(self):
        return self.__repr__()


class LiteralToken(Token):
    pass


class LeftCurlyBraceToken(Token):

    def __init__(self, line_num):
        super(LeftCurlyBraceToken, self).__init__(line_num, '{')


class RightCurlyBraceToken(Token):

    def __init__(self, line_num):
        super(RightCurlyBraceToken, self).__init__(line_num, '}')


class LeftSquareBraceToken(Token):

    def __init__(self, line_num):
        super(LeftSquareBraceToken, self).__init__(line_num, '[')


class RightSquareBraceToken(Token):

    def __init__(self, line_num):
        super(RightSquareBraceToken, self).__init__(line_num, ']')


class ColonToken(Token):

    def __init__(self, line_num):
        super(ColonToken, self).__init__(line_num, ':')


class CommaToken(Token):

    def __init__(self, line_num):
        super(CommaToken, self).__init__(line_num, ',')


class NumberLiteralToken(LiteralToken):

    def __init__(self, line_num, body=''):
        super(NumberLiteralToken, self).__init__(line_num, body)


class StringLiteralToken(LiteralToken):

    def __init__(self, line_num, body, delimiter="'"):
        self.delimiter = delimiter
        super(StringLiteralToken, self).__init__(line_num, body)

    def show(self):
        return '"%s"' % (self.body.replace('"', '\\"'))

    def __str__(self):
        return "<StringLiteralToken: %s>" % self.body


class AssignmentOperatorToken(BinaryOperatorToken):

    def get_node(self, line_num, left, right):
        return nodes.AssignmentNode(line_num, left, right)

    def __init__(self, line_num):
        super(AssignmentOperatorToken, self).__init__(line_num, 14, '=',
                                                      OperatorToken.RIGHT)


class ComparisonOperatorToken(BinaryOperatorToken):

    def get_node(self, line_num, left, right):
        return nodes.ComparisonNode(line_num, left, right)

    def __init__(self, line_num):
        super(ComparisonOperatorToken, self).__init__(line_num, 7, '==')


class AdditionOperatorToken(BinaryOperatorToken):

    def get_node(self, line_num, left, right):
        return nodes.AdditionNode(line_num, left, right)

    def __init__(self, line_num):
        super(AdditionOperatorToken, self).__init__(line_num, 4, '+')


class SubtractionOperatorToken(BinaryOperatorToken):

    def get_node(self, line_num, left, right):
        return nodes.SubtractionNode(line_num, left, right)

    def __init__(self, line_num):
        super(SubtractionOperatorToken, self).__init__(line_num, 4, '-')


class NegationOperatorToken(UnaryOperatorToken):

    def get_node(self, line_num, target):
        return nodes.NegationNode(line_num, target)

    def __init__(self, line_num):
        super(NegationOperatorToken, self).__init__(line_num, 2, 'u-',
                                                    OperatorToken.RIGHT, True)


class DivisionOperatorToken(BinaryOperatorToken):

    def get_node(self, line_num, left, right):
        return nodes.DivisionNode(line_num, left, right)

    def __init__(self, line_num):
        super(DivisionOperatorToken, self).__init__(line_num, 3, '/')


class MultiplicationOperatorToken(BinaryOperatorToken):

    def get_node(self, line_num, left, right):
        return nodes.MultiplicationNode(line_num, left, right)

    def __init__(self, line_num):
        super(MultiplicationOperatorToken, self).__init__(line_num, 3, '*')


class ExponentOperatorToken(BinaryOperatorToken):

    def get_node(self, line_num, left, right):
        return nodes.ExponentNode(line_num, left, right)

    def __init__(self, line_num):
        super(ExponentOperatorToken, self).__init__(line_num, 2, '**',
                                                    OperatorToken.RIGHT)


class GreaterThanOperatorToken(BinaryOperatorToken):

    def get_node(self, line_num, left, right):
        return nodes.GreaterThanNode(line_num, left, right)

    def __init__(self, line_num):
        super(GreaterThanOperatorToken, self).__init__(line_num, 6, '>')


class LessThanOperatorToken(BinaryOperatorToken):

    def get_node(self, line_num, left, right):
        return nodes.LessThanNode(line_num, left, right)

    def __init__(self, line_num):
        super(LessThanOperatorToken, self).__init__(line_num, 6, '<')


class GreaterThanEqualOperatorToken(BinaryOperatorToken):

    def get_node(self, line_num, left, right):
        return nodes.GreaterThanEqualNode(line_num, left, right)

    def __init__(self, line_num):
        super(GreaterThanEqualOperatorToken, self).__init__(line_num, 6, '>=')


class LessThanEqualOperatorToken(BinaryOperatorToken):

    def get_node(self, line_num, left, right):
        return nodes.LessThanEqualNode(line_num, left, right)

    def __init__(self, line_num):
        super(LessThanEqualOperatorToken, self).__init__(line_num, 6, '<=')


class DotNotationOperatorToken(BinaryOperatorToken):

    def get_node(self, line_num, left, right):
        return nodes.DotNotationNode(line_num, left, right)

    def __init__(self, line_num):
        super(DotNotationOperatorToken, self).__init__(line_num, 1, '.')


class LeftParenToken(BinaryOperatorToken):

    def get_node(self, line_num, left, right):
        assert False

    def __init__(self, line_num):
        super(LeftParenToken, self).__init__(line_num, 1, '(')


class RightParenToken(BinaryOperatorToken):

    def get_node(self, line_num, left, right):
        assert False

    def __init__(self, line_num):
        super(RightParenToken, self).__init__(line_num, 9, ')')
