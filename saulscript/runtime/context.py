from decimal import Decimal
import datetime
import logging
from .. import exceptions
from ..syntax_tree import SyntaxTree
from ..lexer import Lexer


class Context(dict):

    def __init__(self, *args, **kwargs):
        self.return_value = None
        self.initialize_globals()
        self.operations_counted = 0
        self.operation_limit = -1
        self.time_limit = -1
        self.start_time = datetime.datetime.now()
        super(Context, self).__init__(self, *args, **kwargs)

    def set_op_limit(self, num):
        self.operation_limit = num

    def set_time_limit(self, seconds):
        self.time_limit = seconds

    def check_limits(self):
        if self.operations_counted > self.operation_limit and \
                self.operation_limit > 0:
            raise exceptions.OperationLimitReached()
        now = datetime.datetime.now()
        delta = now - self.start_time
        if delta.total_seconds() > self.time_limit and \
                self.time_limit > 0:
            raise exceptions.TimeLimitReached()

    def increment_operations(self, num=1):
        self.operations_counted = self.operations_counted + num
        self.check_limits()

    def initialize_globals(self):
        def _print(arg):
            print arg
            return True
        self.bind_function('print', _print)

    def set_return_value(self, node):
        self.return_value = node

    def bind_function(self, name, func):
        if not callable(func):
            raise Exception("Must be callable")
        self[name] = func

    def bind_value(self, name, val):
        if type(val) not in (str, Decimal, dict, list):
            raise Exception("Must be string, decimal, dict, or list")
        self[name] = val

    def execute(self, src):
        new_lexer = Lexer(src)
        tokens = new_lexer.run()
        logging.debug("%s", tokens)
        st = SyntaxTree(Context, tokens)
        st.run()
        st.execute(self)
        return True

