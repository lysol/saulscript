
class SaulException(Exception):

    def __repr__(self):
        base_repr = super(SaulException, self).__repr__()
        return "%s at line %d" % (base_repr, self.line_num)

    def __init__(self, line_num, *args, **kwargs):
        self.line_num = line_num
        super(SaulException, self).__init__(self, *args, **kwargs)


class ParseError(SaulException):
    pass


class EndContextExecution(SaulException):
    pass


class OutOfTokens(SaulException):
    pass


class ReturnRequestedException(SaulException):
    pass


class ObjectResolutionError(SaulException):
    pass


class EndOfFileException(Exception):
    pass


class SaulRuntimeError(SaulException):
    pass


class OperationLimitReached(SaulException):
    pass


class TimeLimitReached(SaulException):
    pass
