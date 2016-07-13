__all__ = ['CRESTException', 'InvalidPathException', 'AuthenticationException',
    'PathNoLongerSupportedException', 'TooManyAttemptsException', 'AuthenticationFailedException']


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


class PathNoLongerSupportedException(CRESTException):

    def __init__(self, url):
        super(PathNoLongerSupportedException, self).__init__(url)


class TooManyAttemptsException(CRESTException):

    def __init__(self, url):
        super(TooManyAttemptsException, self).__init__(url)


class AuthenticationFailedException(CRESTException):

    def __init__(self, message):
        super(AuthenticationFailedException, self).__init__('')
        self.message = message


class AccessTokenExpiredException(CRESTException):

    def __init__(self, message):
        super(AccessTokenExpiredException, self).__init__('')
        self.message = 'The access token has expired and no refresh token is present'
