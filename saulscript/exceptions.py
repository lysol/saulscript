
class SaulException(Exception):

    def __str__(self):
        return self.__repr__()

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


class UnexpectedCharacter(SaulException):

    def __init__(self, line_num, char, *args, **kwargs):
        self.char = char
        super(UnexpectedCharacter, self).__init__(line_num, *args, **kwargs)
        self.message = self.__repr__()

    def __repr__(self):
        return 'Unexpected character (%s) at line %d' % \
            (self.char, self.line_num)
