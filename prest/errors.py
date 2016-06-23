__all__ = ['CRESTException', 'InvalidPathException', 'AuthenticationException', 'PathNoLongerSupported']


class CRESTException(Exception):

    def __init__(self, url):
        self.url = url

    def __repr__(self):
        return '<{}-{}>'.format(self.__class__.__name__, self.url)


class InvalidPathException(CRESTException):

    def __init__(self, url):
        super(InvalidPathException, self).__init__(url)


class AuthenticationException(CRESTException):

    def __init__(self, url):
        super(AuthenticationException, self).__init__(url)


class PathNoLongerSupported(CRESTException):

    def __init__(self, url):
        super(PathNoLongerSupported, self).__init__(url)
