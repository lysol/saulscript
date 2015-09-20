

class Context(dict):

    def __init__(self, *args, **kwargs):
        self.return_value = None
        super(Context, self).__init__(self, *args, **kwargs)

    def set_return_value(self, node):
        self.return_value = node