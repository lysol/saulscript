import lexer
import ast
import logging
from context import Context


class Context(dict):

    def __init__(self, *args, **kwargs):
        self.return_value = None
        super(Context, self).__init__(self, *args, **kwargs)

    def set_return_value(self, node):
        self.return_value = node


class Runtime(object):

    def __init__(self):
        self.context = Context()

    def execute(self, src):
        new_lexer = lexer.Lexer(src)
        tokens = new_lexer.run()
        logging.debug("%s", tokens)
        new_ast = ast.AST(tokens)
        new_ast.run()
        context = Context()
        return new_ast.execute(context)
