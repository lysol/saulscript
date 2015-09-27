from decimal import Decimal
import operator
import logging
from .. import exceptions

class Node(object):

    def __init__(self, line_num):
        self.line_num = line_num
        pass

    def __str__(self):
        return self.__repr__()


class NopNode(Node):

    def reduce(self, context):
        context.increment_operations()
        return None

    def __repr__(self):
        return '<nop>'


class LiteralNode(Node):

    def __init__(self, line_num, value):
        super(LiteralNode, self).__init__(line_num)
        self.value = value

    def __repr__(self):
        return '{%s}' % self.value

    def reduce(self, context):
        context.increment_operations()
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
            except exceptions.ReturnRequestedException:
                break
            except exceptions.EndContextExecution:
                break
        return context.return_value


class IfNode(Node):

    def __init__(self, line_num, condition, then=[], else_branch=[]):
        self.condition = condition
        if then == []:
            then = Branch([])
        if else_branch == []:
            else_branch = Branch([])
        self.then_branch = then
        self.else_branch = else_branch
        super(IfNode, self).__init__(line_num)

    def add_then(self, then_statement):
        self.then_branch.append(then_statement)

    def add_else(self, else_statement):
        self.else_branch.append(else_statement)

    def __repr__(self):
        return '<If: %s Then: %s Else: %s>' % \
            (self.condition, self.then_branch, self.else_branch)

    def reduce(self, context):
        context.increment_operations()
        result = self.condition.reduce(context)
        logging.debug("If result: %s", result)
        if result:
            return self.then_branch.execute(context)
        elif len(self.else_branch) > 0:
            return self.else_branch.execute(context)


class WhileNode(Node):

    def __init__(self, line_num, condition, branch=Branch()):
        self.condition = condition
        self.branch = branch
        super(WhileNode, self).__init__(line_num)

    def __repr__(self):
        return "<while %s: %s>" % (self.condition, self.branch)

    def reduce(self, context):
        context.increment_operations()
        logging.debug("Running while loop")
        while True:
            result = self.condition.reduce(context)
            logging.debug("While result: %s" % result)
            if not result:
                break
            self.branch.execute(context)
        return context


class ForNode(Node):

    def __init__(self, line_num, local_name, iterable, branch=Branch()):
        self.local_name = local_name
        self.iterable = iterable
        self.branch = branch
        super(ForNode, self).__init__(line_num)

    def __repr__(self):
        return "<for %s in %s: %s>" % \
            (self.local_name, self.iterable, self.branch)

    def reduce(self, context):
        context.increment_operations()
        logging.debug("Running for loop")
        for item in self.iterable.reduce(context):
            # same as python. variable is set in the outer context
            context[self.local_name] = item
            self.branch.execute(context)


class UnaryOpNode(Node):

    def __init__(self, line_num, target):
        self.target = target
        super(UnaryOpNode, self).__init__(line_num)

    def operation(self, target):
        raise NotImplementedError(
            "Please define the operation of this operator")

    def reduce(self, context):
        context.increment_operations()
        logging.debug("%s %s", self.__class__, type(self.target))
        return self.operation(self.target.reduce(context), context)

    def __repr__(self):
        return "<unary-op %s>" % repr(self.target)


class BinaryOpNode(Node):

    def __init__(self, line_num, left, right):
        self.left = left
        self.right = right
        super(BinaryOpNode, self).__init__(line_num)

    def reduce(self, context):
        context.increment_operations()
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
        context.increment_operations()
        logging.debug("AssignmentNode: I am a %s" % self)
        logging.debug("AssignmentNode: %s %s", self.left, self.right)
        result = self.right.reduce(context)
        logging.debug("Assignment result: %s" % result)
        if not isinstance(self.left, SubscriptNotationNode):
            context[self.left.name] = result
        else:
            # This dict member doesn't exist yet, set it.
            subscript = self.left
            # context[object.name][stuff in []] = our right result
            context[subscript.left.name][subscript.right.value] = result


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

    def __init__(self, line_num, number_string):
        self.value = Decimal(number_string)
        self.line_num = line_num

    def reduce(self, context):
        context.increment_operations()
        return self.value


class StringNode(LiteralNode):

    def __init__(self, line_num, string):
        logging.debug("Assigning '%s' to %s" % (string, self.__class__))
        super(StringNode, self).__init__(line_num, string)

    def reduce(self, context):
        context.increment_operations()
        return self.value


class VariableNode(LiteralNode):

    def reduce(self, context):
        context.increment_operations()
        if self.name in context:
            return context[self.name]
        else:
            raise exceptions.ObjectResolutionError(self.line_num, "No variable named %s" % self.name)

    def __init__(self, line_num, name):
        self.name = name
        super(VariableNode, self).__init__(line_num, name)


class BooleanNode(Node):

    def __init__(self, line_num, value):
        self.value = value
        super(BooleanNode, self).__init__(line_num)

    def reduce(self, context):
        return bool(self.value)


class SubscriptNotationNode(BinaryOpNode):

    def reduce(self, context):
        context.increment_operations()
        logging.debug("Reducing subscript notation")
        if not isinstance(self.left, DictionaryNode) and \
                not isinstance(self.left, ListNode):
            raise exceptions.SaulRuntimeError(self.line_num,
                "Subscript notation must be used with a "
                "list or dictionary (Got %s)" % self.left.__class__)
        index = self.right.reduce(context)
        return self.left.reduce(context)[index]


class DotNotationNode(BinaryOpNode):

    def reduce(self, context):
        logging.debug("Context: ", context)
        context.increment_operations()
        logging.debug("Resolving dot notation")
        dictthing = self.left.reduce(context)
        if type(dictthing) != dict:
            raise exceptions.SaulRuntimeError(self.line_num,
                "Dot notation used with non-dictionary: %s" %
                dictthing)
        try:
            return dictthing[self.right.name]
        except KeyError:
            raise exceptions.SaulRuntimeError(self.line_num,
                                              "No key named %s in %s" %
                                              (self.right.name, dictthing))


class DictionaryNode(dict):

    def __init__(self, line_num, *args, **kwargs):
        self.line_num = line_num
        super(DictionaryNode, self).__init__(*args, **kwargs)

    def reduce(self, context):
        context.increment_operations()
        logging.debug("Reducing dictionary")
        return {k: self[k].reduce(context) for k in self}

    def __repr__(self):
        return "{%s}" % ", ".join(
            ["%s: %s" % (k, v) for k, v in self.iteritems()])

    def __str__(self):
        return self.__repr__()


class ListNode(list):

    def reduce(self, context):
        context.increment_operations()
        return [item.reduce(context) for item in self]

    def get_node(self):
        return self


class FunctionNode(Node):

    def __init__(self, line_num, context_class, signature=[], branch=Branch()):
        self.branch = branch
        self.signature = signature
        self.context_class = context_class
        super(FunctionNode, self).__init__(line_num)

    def reduce(self, context):
        context.increment_operations()

        def closure(*args):
            logging.debug("Arguments supplied during closure: %s" % repr(args))
            context.reset_start_time()
            # Copy the function's context so assignments
            # are thrown away when done
            execution_context = self.context_class()
            execution_context.update(context)
            logging.debug("This function's execution context is %s" %
                          execution_context)
            # include the function arguments
            # in the current execution context
            for index, name_identifier in enumerate(self.signature):
                # grab the argument from the invocation's
                # argument list, reduce each of them,
                # and set the execution context item that
                # corresponds to this function's signature
                logging.debug("Examining function argument: %d, %s", index, name_identifier)
                try:
                    execution_context[name_identifier] = \
                        args[index].reduce(context)
                except IndexError:
                    raise exceptions.SaulRuntimeError(self.line_num,
                        "Not enough arguments supplied.")
                except AttributeError:
                    logging.debug("Received AttributeError, which means the value is a Python value. (%s)", name_identifier)
                    logging.debug("repr of the value: %s", repr(args[index]))
                    execution_context[name_identifier] = args[index]
            # execute the branch
            logging.debug("Execution context after argument binding: %s", repr(execution_context))
            return_node = self.branch.execute(execution_context)
            # add the result here
            logging.debug("Function executed. Result: %s\nIncrementing operations", return_node)
            context.increment_operations(execution_context.operations_counted)
            return return_node
        logging.debug("Returning closure")
        return closure

    def __str__(self):
        arglist = ", ".join(self.signature)
        return "<function(%s) %s>" % (arglist, self.branch)

    def __repr__(self):
        return self.__str__()


class BoundFunctionNode(Node):

    def __init__(self, line_num, func):
        self.func = func
        super(BoundFunctionNode, self).__init__(line_num)

    def reduce(self, context):
        context.increment_operations()
        logging.debug("Reducing bound function")

        def _func(*_args):
            args = [arg.reduce(context) for arg in _args]
            return self.func(*args)
        return _func


class ReturnNode(Node):

    def __init__(self, line_num, return_node):
        self.return_node = return_node
        super(ReturnNode, self).__init__(line_num)

    def reduce(self, context):
        context.increment_operations()
        context.set_return_value(self.return_node.reduce(context))
        raise exceptions.ReturnRequestedException(self.line_num)

    def __repr__(self):
        return '<return %s>' % self.return_node


class InvocationNode(Node):

    def __init__(self, line_num, callable_name, arg_list):
        self.callable_name = callable_name
        self.arg_list = arg_list
        super(InvocationNode, self).__init__(line_num)

    def reduce(self, context):
        context.increment_operations()
        if self.callable_name not in context:
            raise exceptions.SaulRuntimeError("%s is not defined" % self.callable_name)
        callable_item = context[self.callable_name]
        logging.debug("Checking %s to see if it is callable" % callable_item)
        if not callable(callable_item):
            raise exceptions.SaulRuntimeError(self.line_num, "%s is not callable" %
                                              callable_item)
        return callable_item(*self.arg_list)

    def __repr__(self):
        arglist = ", ".join([repr(a) for a in self.arg_list])
        return '<invoke %s(%s)>' % (self.callable_name, arglist)
