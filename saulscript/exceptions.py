
class ParseError(Exception):
    pass


class EndContextExecution(Exception):
    pass


class OutOfTokens(Exception):
    pass


class ReturnRequestedException(Exception):
    pass


class ObjectResolutionError(Exception):
    pass


class EndOfFileException(Exception):
    pass


class SaulRuntimeError(Exception):
    pass


class OperationLimitReached(Exception):
    pass


class TimeLimitReached(Exception):
    pass
