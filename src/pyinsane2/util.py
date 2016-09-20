__all__ = [
    'PyinsaneException',
]

class PyinsaneException(Exception):
    def __init__(self, status):
        Exception.__init__(self, str(status))
        self.status = status