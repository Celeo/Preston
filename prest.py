import requests


class Prest:
    base_url = 'https://crest-tq.eveonline.com'
    path = ''

    def __init__(self, path=None):
        self.path = path or ''

    def __getattr__(self, target):
        print('Call to "{}"'.format(target))
        return Prest('{}/{}'.format(self.path, target))

    def __call__(self):
        r = requests.get(self.base_url + self.path)
        if r.status_code == 404:
            raise InvalidPathException(self.base_url + self.path)
        if r.status_code == 403:
            raise AuthenticationException(self.base_url + self.path)
        if r.status_code == 406:
            raise PathNoLongerSupported(self.base_url + self.path)

    def __repr__(self):
        return '<Prest-{}>'.format(self.path)


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
