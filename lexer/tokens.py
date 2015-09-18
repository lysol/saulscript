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


class LineTerminatorToken(Token):

    def __init__(self):
        super(LineTerminatorToken, self).__init__("\n")


class BinaryOperatorToken(Token):

    def get_node(self):
        raise NotImplementedError("Please define a type of node for this token to return")

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

    def get_node(self, left, right):
        return ast.nodes.AssignmentNode(left, right)

    def __init__(self):
        super(AssignmentOperatorToken, self).__init__(14, '=')


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
        super(ExponentOperatorToken, self).__init__(2, '**')


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
