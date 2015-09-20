from decimal import Decimal
from context import Context
import operator
import logging
import ast


class ReturnRequestedException(Exception):
    pass


class ObjectResolutionError(Exception):
    pass


class Node(object):

    def __init__(self):
        pass

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


class Branch(list):

    def __init__(self, *args, **kwargs):
        self.return_value = None
        super(Branch, self).__init__(*args, **kwargs)

    def __repr__(self):
        return '[%s]' % (", ".join(map(lambda i: i.__repr__(), self)))

    def set_return(self, node):
        self.return_value = node

    def execute(self, context):
        for node in self:
            try:
                node.reduce(context)
            except ReturnRequestedException:
                break
            except ast.EndContextExecution:
                break
        return context.return_value


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
        return '<If: %s Then: %s Else: %s>' % \
            (self.condition, self.then_branch, self.else_branch)

    def reduce(self, context):
        result = self.condition.reduce(context)
        logging.debug("If result: %s", result)
        if result:
            return self.then_branch.execute(context)
        elif len(self.else_branch) > 0:
            return self.else_branch.execute(context)


class UnaryOpNode(Node):

    def __init__(self, target):
        self.target = target

    def operation(self, target):
        raise NotImplementedError(
            "Please define the operation of this operator")

    def reduce(self, context):
        logging.debug("%s %s", self.__class__, type(self.target))
        return self.operation(self.target.reduce(context), context)

    def __repr__(self):
        return "<unary-op %s>" % repr(self.target)


class BinaryOpNode(Node):

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def reduce(self, context):
        logging.debug("%s %s %s",
                      self.__class__, type(self.left),
                      type(self.right))
        return self.operation(self.left.reduce(context),
                              self.right.reduce(context), context)

    def operation(self, left, right):
        raise NotImplementedError(
            "Please define the operation of this operator")

    def __repr__(self):
        return "<%s %s %s>" % (repr(self.left), 'binary-op', repr(self.right))


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
        logging.debug("%s %s", left, right)
        return operator.div(left, right)


class ExponentNode(BinaryOpNode):

    def operation(self, left, right, context):
        return operator.pow(left, right)


class AssignmentNode(BinaryOpNode):

    def reduce(self, context):
        logging.debug("%s %s", self.left, self.right)
        context[self.left.name] = self.right.reduce(context)


class ComparisonNode(BinaryOpNode):

    def operation(self, left, right, context):
        logging.debug("Left: %s   Right: %s", repr(left), repr(right))
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


class NegationNode(UnaryOpNode):

    def operation(self, target, context):
        return operator.mul(-1, target)


class NumberNode(LiteralNode):

    def __init__(self, number_string):
        self.value = Decimal(number_string)

    def reduce(self, context):
        return self.value


class StringNode(LiteralNode):

    def __init__(self, string):
        self.value = unicode(string)


class VariableNode(LiteralNode):

    def reduce(self, context):
        if self.name in context:
            return context[self.name]
        else:
            raise NameError("No variable named %s" % self.name)

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


class DictionaryNode(Node):

    def __init__(self):
        super(DictionaryNode, self).__init__()
        self.data = {}

    def set_item(self, name, value):
        self.data[name] = value

    def get_item(self, name):
        return self.data[name]

    def reduce(self, context):
        return {k: self.data[k].reduce(context) for k in self.data}

    def __repr__(self):
        return "{%s}" % ", ".join(["%s: %s" % (k, v) for k, v in self.data.iteritems()])


class ListNode(list):

    def reduce(self, context):
        return [item.reduce(context) for item in self]

    def get_node(self):
        return self


class FunctionNode(Node):

    def __init__(self, signature=[], branch=Branch(), context={}):
        self.context = context
        self.branch = branch
        self.signature = signature

    def reduce(self, context):
        def closure(*args):
            # Copy the function's context so assignments are thrown away when done
            execution_context = Context()
            execution_context.update(self.context) 
            # include the function arguments in the current execution context
            for index, name_identifier in enumerate(self.signature):
                # grab the argument from the invocation's argument list, reduce each of them,
                # and set the execution context item that corresponds to this function's signature
                try:
                    execution_context[name_identifier] = args[index].reduce(context)
                except IndexError:
                    raise SaulRuntimeError("Not enough arguments supplied.")
            # execute the branch
            return_node = self.branch.execute(execution_context)
            return return_node
        return closure


class ReturnNode(Node):

    def __init__(self, return_node):
        self.return_node = return_node

    def reduce(self, context):
        context.set_return_value(self.return_node.reduce(context))
        raise ReturnRequestedException()


class InvocationNode(Node):

    def __init__(self, callable_name, arg_list):
        self.callable_name = callable_name
        self.arg_list = arg_list

    def reduce(self, context):
        if self.callable_name not in context:
            raise NameError("%s is not defined" % self.callable_name)
        callable_item = context[self.callable_name]
        if not callable(callable_item):
            raise SaulRuntimeError("%s is not callable" % callable_item)
        return callable_item(*self.arg_list)
