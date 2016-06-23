import requests

from prest.errors import *


# TODO: see Design.md

__all__ = ['Prest', 'APIElement']


class Prest:
    base_uri = 'https://crest-tq.eveonline.com'
    path = ''

    def __init__(self, path=None):
        self.path = path or ''
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Prest v0.0.1',
            'Accept': 'application/json'
        })

    def __getattr__(self, target):
        print('Call to "{}"'.format(target))
        return APIElement('{}/{}'.format(self.path, target))

    def __call__(self):
        r = self.session.get(self.base_uri + self.path)
        if r.status_code == 404:
            raise InvalidPathException(self.base_uri + self.path)
        if r.status_code == 403:
            raise AuthenticationException(self.base_uri + self.path)
        if r.status_code == 406:
            raise PathNoLongerSupported(self.base_uri + self.path)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return '<Prest-{}>'.format(self.path)


class APIElement:

    def __init__(self, uri):
        self.uri = uri
