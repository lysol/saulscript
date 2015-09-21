import ast
import ast.nodes


class DeferredReference(object):

    def resolve(self, value):
        self.parent[name] = value
        return value

    def __init__(self, name, parent):
        self.parent = parent


class Context(dict):

    def __init__(self, *args, **kwargs):
        self.return_value = None
        super(Context, self).__init__(self, *args, **kwargs)

    def set_return_value(self, node):
        self.return_value = node