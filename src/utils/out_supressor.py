import sys

class NullWriter(object):
    """A class that suppresses output to stdout and stderr."""
    def write(self, _):
        pass

    def flush(self):
        pass

def suppress_output(function, *args, **kwargs):
    oldstout = sys.stdout
    nullwriter = NullWriter()

    sys.stdout = nullwriter
    res = function(*args, **kwargs)
    sys.stdout = oldstout

    return res
