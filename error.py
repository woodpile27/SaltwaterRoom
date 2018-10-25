class FileFormatError(Exception):

    def __init__(self, file):
        Exception.__init__(self)
        self.file = file

    def __str__(self):
        return "FileFormatError: %s cannot be matched by os" % self.file

class FileExecuteError(Exception):

    def __init__(self, file):
        Exception.__init__(self)
        self.file = file

    def __str__(self):
        return "FileExecuteError: %s execution failed" % self.file

