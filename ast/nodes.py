from node import *
from decimal import *


class SaulRuntimeError(Exception):

    def __init__(self, message):
        self.message = message


class IfNode(Node):

    def __init__(self, condition, then=[], else_branch=[]):
        self.condition = condition
        if then == []:
            then = Branch([])
        if else_branch == []:
            else_branch = Branch([])
        self.then_branch = then
        self.else_branch = else_branch

    def add_then(self, then_statement):
        self.then_branch.append(then_statement)

    def add_else(self, else_statement):
        self.else_branch.append(else_statement)

    def __repr__(self):
        return '<If: %s Then: %s Else: %s>' % (self.condition, self.then_branch, self.else_branch)

    def execute(self, context):
        result = self.condition.reduce(context)
        if result:
            return self.then_branch.execute(context)
        elif len(self.else_branch) > 0:
            return self.else_branch.extecute(context)


class BinaryOpNode(Node):

    operator = None

    def set_left(self, node):
        self.branches[0] = node

    def set_right(self, node):
        self.branches[2] = node

    def __init__(self, left, right):
        self.left = left
        self.right = right
        assert self.operator is not None

    def operate(self, context):
        raise NotImplementedError('Please define what this operator does.')

    def __repr__(self):
        return "<%s %s %s>" % (repr(self.left), self.operator, repr(self.right))


class AdditionNode(BinaryOpNode):

    operator = '+'

    def operate(self, context):
        if isinstance(self.left, NumberNode):
            if not isinstance(self.right, NumberNode):
                raise SaulRuntimeError('Type mismatch')
            return self.left.value + self.right.value


class SubtractionNode(BinaryOpNode):

    operator = '-'

    def operate(self, context):
        if isinstance(self.left, NumberNode):
            if not isinstance(self.right, NumberNode):
                raise SaulRuntimeError('Type mismatch')
            return self.left.value - self.right.value


class MultiplicationNode(BinaryOpNode):

    operator = '*'

    def operate(self, context):
        if isinstance(self.left, NumberNode):
            if not isinstance(self.right, NumberNode):
                raise SaulRuntimeError('Type mismatch')
            return self.left.value * self.right.value


class DivisionNode(BinaryOpNode):

    operator = '/'

    def operate(self, context):
        if isinstance(self.left, NumberNode):
            if not isinstance(self.right, NumberNode):
                raise SaulRuntimeError('Type mismatch')
            return self.left.value / self.right.value


class ExponentNode(BinaryOpNode):

    operator = '**'

    def operate(self, context):
        if isinstance(self.left, NumberNode):
            if not isinstance(self.right, NumberNode):
                raise SaulRuntimeError('Type mismatch')
            return self.left.value ** self.right.value


class NumberNode(LiteralNode):

    def __init__(self, number_string):
        self.value = Decimal(number_string)


class StringNode(LiteralNode):

    def __init__(self, string):
        self.value = unicode(string)


class VariableNode(LiteralNode):

    def __init__(self, name):
        self.value = name


class BooleanNode(Node):

    def __init__(self, value):
        self.value = value