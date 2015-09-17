class Node(object):

    def __init__(self):
        pass

    def _make_dump_arrow(self, string, level):
        return "%s%s" % ('> ' * level, string)

    def __str__(self):
        return self.__repr__()


class NopNode(Node):

    def __repr__(self):
        return '<nop>'


class LiteralNode(Node):

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return '{%s}' % self.value


class StringLiteralNode(LiteralNode):
    pass


class NumberLiteralNode(LiteralNode):
    pass


class VariableNode(Node):

    def __init__(self, name):
        self.name = name


class Branch(list):

    def _make_dump_arrow(self, string, level):
        return "%s%s" % ('> ' * level, string)

    def __repr__(self):
        return '[%s]' % (", ".join(map(lambda i: i.__repr__(), self)))

    def execute(self, context):
        for node in self:
            node.execute(context)
        return context
