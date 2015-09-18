from decimal import Decimal
import operator

class ObjectResolutionError(Exception):
    pass

class Node(object):

    def __init__(self):
        pass

    def _make_dump_arrow(self, string, level):
        return "%s%s" % ('> ' * level, string)

    def __str__(self):
        return self.__repr__()


class NopNode(Node):

    def reduce(self, context):
        return None

    def __repr__(self):
        return '<nop>'


class LiteralNode(Node):

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return '{%s}' % self.value

    def reduce(self, context):
        return self.value


class VariableNode(Node):

    def __init__(self, name):
        self.name = name

    def reduce(self, context):
        if self.name in context:
            return context[self.name]
        else:
            raise NameError("%s is not defined" % self.name)


class Branch(list):

    def _make_dump_arrow(self, string, level):
        return "%s%s" % ('> ' * level, string)

    def __repr__(self):
        return '[%s]' % (", ".join(map(lambda i: i.__repr__(), self)))

    def execute(self, context):
        for node in self:
            node.reduce(context)
        return context


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

    def reduce(self, context):
        result = self.condition.reduce(context)
        if result:
            return self.then_branch.execute(context)
        elif len(self.else_branch) > 0:
            return self.else_branch.execute(context)


class BinaryOpNode(Node):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def reduce(self, context):
        print type(self.left), type(self.right)
        return self.operation(self.left.reduce(context), self.right.reduce(context), context)

    def operation(self, left, right):
        raise NotImplementedError("Please define the operation of this operator")

    def __repr__(self):
        return "<%s %s %s>" % (repr(self.left), 'op', repr(self.right))


class AdditionNode(BinaryOpNode):

    def operation(self, left, right, context):
        return operator.add(left, right)


class SubtractionNode(BinaryOpNode):

    def operation(self, left, right, context):
        return operator.sub(left, right)


class MultiplicationNode(BinaryOpNode):

    def operation(self, left, right, context):
        return operator.mul(left, right)


class DivisionNode(BinaryOpNode):

    def operation(self, left, right, context):
        print left, right
        return operator.div(left, right)


class ExponentNode(BinaryOpNode):

    def operation(self, left, right, context):
        return operator.pow(left, right)


class AssignmentNode(BinaryOpNode):

    def reduce(self, context):
        print self.left, self.right
        context[self.left.name] = self.right.reduce(context)


class ComparisonNode(BinaryOpNode):

    def operation(self, left, right, context):
        return operator.eq(left, right)


class LessThanNode(BinaryOpNode):

    def operation(self, left, right, context):
        return operator.lt(left, right)


class GreaterThanNode(BinaryOpNode):

    def operation(self, left, right, context):
        return operator.gt(left, right)


class GreaterThanEqualToNode(BinaryOpNode):

    def operation(self, left, right, context):
        return operator.ge(left, right)


class LessThanEqualToNode(BinaryOpNode):

    def operation(self, left, right, context):
        return operator.le(left, right)


class NumberNode(LiteralNode):

    def __init__(self, number_string):
        self.value = Decimal(number_string)

    def reduce(self, context):
        return self.value


class StringNode(LiteralNode):

    def __init__(self, string):
        self.value = unicode(string)


class VariableNode(LiteralNode):

    def __init__(self, name):
        self.name = name
        self.value = name


class BooleanNode(Node):

    def __init__(self, value):
        self.value = value


class DotNotationNode(BinaryOpNode):

    def operation(self, left, right, context):
        if not isinstance(left, VariableNode):
            raise ObjectResolutionError()

        return context[left.name].reduce()[right.name].reduce()