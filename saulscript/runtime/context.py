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
        self.reset_start_time()
        super(Context, self).__init__(self, *args, **kwargs)

    def reset_start_time(self):
        logging.debug("Resetting start time")
        self.start_time = datetime.datetime.now()

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
            raise exceptions.TimeLimitReached(delta.total_seconds())

    def increment_operations(self, num=1):
        self.operations_counted = self.operations_counted + num
        self.check_limits()

    def initialize_globals(self):
        pass

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

    def execute(self, src, op_limit=-1, time_limit=-1):
        self.reset_start_time()
        new_lexer = Lexer(src)
        tokens = new_lexer.run()
        logging.debug("%s", tokens)
        st = SyntaxTree(Context, tokens)
        st.run()
        st.execute(self, op_limit=op_limit, time_limit=time_limit)
        return True

    def wrap_function(self, function, reset_start_time=True):
        def _function(*args):
            logging.debug("Wrapped Context: " + self.__repr__())
            if reset_start_time:
                self.reset_start_time()
            _args = []
            for arg in args:
                if hasattr(arg, 'reduce'):
                    logging.debug("Reducing %s" % arg)
                    _args.append(arg.reduce(self))
                else:
                    _args.append(arg)
            return function(*_args)
        return _function

    def __repr__(self):
        return '{%s}' % ', '.join(["%s: %s" % (k, v) for k, v in self.iteritems()])
