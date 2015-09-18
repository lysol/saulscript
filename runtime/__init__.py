import lexer
import ast
from context import Context

class Runtime(object):

    def __init__(self):
        self.context = {}

    def execute(self, src):
        new_lexer = lexer.Lexer(src)
        tokens = new_lexer.run()
        new_ast = ast.AST(tokens)
        new_ast.run()
        context = Context()
        return new_ast.execute(context)