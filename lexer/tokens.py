import ast
import ast.nodes


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

    def get_node(self):
        # ha ha this is bad
        return self


class LineTerminatorToken(Token):

    def __init__(self):
        super(LineTerminatorToken, self).__init__("\n")


class OperatorToken(Token):

    LEFT = 0
    RIGHT = 1

    def get_node(self):
        raise NotImplementedError(
            "Please define a type of node for this token to return")

    def __init__(self, precedence, body, associativity=None, unary=False):
        self.precedence = precedence
        self.associativity = associativity \
            if associativity is not None else self.LEFT
        super(OperatorToken, self).__init__(body)
        self.unary = unary


class BinaryOperatorToken(OperatorToken):
    pass


class UnaryOperatorToken(OperatorToken):
    pass


class IdentifierToken(Token):

    def __init__(self, body):
        super(IdentifierToken, self).__init__(body)


class LiteralToken(Token):
    pass


class LeftCurlyBraceToken(Token):

    def __init__(self):
        super(LeftCurlyBraceToken, self).__init__('{')


class RightCurlyBraceToken(Token):

    def __init__(self):
        super(RightCurlyBraceToken, self).__init__('}')


class LeftSquareBraceToken(Token):

    def __init__(self):
        super(LeftSquareBraceToken, self).__init__('[')


class RightSquareBraceToken(Token):

    def __init__(self):
        super(RightSquareBraceToken, self).__init__(']')


class ColonToken(Token):

    def __init__(self):
        super(ColonToken, self).__init__(':')


class CommaToken(Token):

    def __init__(self):
        super(CommaToken, self).__init__(',')


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

    def get_node(self, left, right):
        return ast.nodes.AssignmentNode(left, right)

    def __init__(self):
        super(AssignmentOperatorToken, self).__init__(14, '=',
                                                      OperatorToken.RIGHT)


class ComparisonOperatorToken(BinaryOperatorToken):

    def get_node(self, left, right):
        return ast.nodes.ComparisonNode(left, right)

    def __init__(self):
        super(ComparisonOperatorToken, self).__init__(7, '==')


class AdditionOperatorToken(BinaryOperatorToken):

    def get_node(self, left, right):
        return ast.nodes.AdditionNode(left, right)

    def __init__(self):
        super(AdditionOperatorToken, self).__init__(4, '+')


class SubtractionOperatorToken(BinaryOperatorToken):

    def get_node(self, left, right):
        return ast.nodes.SubtractionNode(left, right)

    def __init__(self):
        super(SubtractionOperatorToken, self).__init__(4, '-')


class NegationOperatorToken(UnaryOperatorToken):

    def get_node(self, target):
        return ast.nodes.NegationNode(target)

    def __init__(self):
        super(NegationOperatorToken, self).__init__(2, 'u-',
                                                    OperatorToken.RIGHT, True)


class DivisionOperatorToken(BinaryOperatorToken):

    def get_node(self, left, right):
        return ast.nodes.DivisionNode(left, right)

    def __init__(self):
        super(DivisionOperatorToken, self).__init__(3, '/')


class MultiplicationOperatorToken(BinaryOperatorToken):

    def get_node(self, left, right):
        return ast.nodes.MultiplicationNode(left, right)

    def __init__(self):
        super(MultiplicationOperatorToken, self).__init__(3, '*')


class ExponentOperatorToken(BinaryOperatorToken):

    def get_node(self, left, right):
        return ast.nodes.ExponentNode(left, right)

    def __init__(self):
        super(ExponentOperatorToken, self).__init__(2, '**',
                                                    OperatorToken.RIGHT)


class GreaterThanOperatorToken(BinaryOperatorToken):

    def get_node(self, left, right):
        return ast.nodes.GreaterThanNode(left, right)

    def __init__(self):
        super(GreaterThanOperatorToken, self).__init__(6, '>')


class LessThanOperatorToken(BinaryOperatorToken):

    def get_node(self, left, right):
        return ast.nodes.LessThanNode(left, right)

    def __init__(self):
        super(LessThanOperatorToken, self).__init__(6, '<')


class GreaterThanEqualOperatorToken(BinaryOperatorToken):

    def get_node(self, left, right):
        return ast.nodes.GreaterThanEqualNode(left, right)

    def __init__(self):
        super(GreaterThanEqualOperatorToken, self).__init__(6, '>=')


class LessThanEqualOperatorToken(BinaryOperatorToken):

    def get_node(self, left, right):
        return ast.nodes.LessThanEqualNode(left, right)

    def __init__(self):
        super(LessThanEqualOperatorToken, self).__init__(6, '<=')


class DotNotationOperatorToken(BinaryOperatorToken):

    def get_node(self, left, right):
        return ast.nodes.DotNotationNode(left, right)

    def __init__(self):
        super(DotNotationOperatorToken, self).__init__(1, '.')


class LeftParenToken(BinaryOperatorToken):

    def get_node(self, left, right):
        assert False

    def __init__(self):
        super(LeftParenToken, self).__init__(1, '(')


class RightParenToken(BinaryOperatorToken):

    def get_node(self, left, right):
        assert False

    def __init__(self):
        super(RightParenToken, self).__init__(9, ')')
