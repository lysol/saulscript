import lexer
import ast


class Runtime(object):

    def __init__(self):
        self.context = {}

    def execute(self, src):
        new_lexer = lexer.Lexer(src)
        new_lexer.run()
        new_ast = ast.AST(lexer.tokens)
        new_ast.run()
