import logging
from ..syntax_tree import SyntaxTree
from ..lexer import Lexer
from .context import Context


class Runtime(object):

    def __init__(self):
        pass

    def execute(self, src):
        new_lexer = Lexer(src)
        tokens = new_lexer.run()
        logging.debug("%s", tokens)
        st = SyntaxTree(tokens)
        st.run()
        context = Context()
        return st.execute(context)
