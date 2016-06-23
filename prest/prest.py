import logging
import sys

import requests

from prest.errors import *


__all__ = ['Prest', 'APIElement']
base_uri = 'https://crest-tq.eveonline.com'


class Prest:

    def __init__(self, version=None, **kwargs):
        self.__configure_logger(**kwargs)
        self.data = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Prest v0.0.1',
            'Accept': 'application/json'
        })
        if version:
            self.session.headers.update({
                'Version': version
            })
        self()

    def __configure_logger(self, **kwargs):
        self.logger = logging.getLogger('prest')
        self.logger.setLevel(kwargs.get('logging_level', logging.ERROR))
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(style='{', fmt='{asctime} [{levelname}] {message}', datefmt='%Y-%m-%d %H:%M:%S'))
        handler.setLevel(kwargs.get('logging_level', logging.ERROR))
        self.logger.addHandler(handler)

    @property
    def version(self):
        return self.session.headers.get('Version')

    @version.setter
    def version(self, value):
        self.session.headers.update({
            'Version': version
        })

    def __getattr__(self, target):
        if not self.data:
            self()
        self.logger.debug('Root attrib to "{}"'.format(target))
        return APIElement('', self.data[target], self)

    def __call__(self):
        self.logger.debug('Root call')
        self.data = self.session.get(base_uri).json()

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return '<Prest-{}>'.format(self.path)


class APIElement:
    # TODO: subclass dict and use the internal storage to cache?

    def __init__(self, uri, data, prest):
        self.uri = uri
        self.data = data
        self.prest = prest
        self.session = prest.session
        self.logger = prest.logger
        self.logger.debug('APIElement init: "{}"'.format(self.uri))

    def __call__(self):
        self.logger.debug('Element call, uri = "{}"'.format(self.uri))
        if self.data:
            self.logger.debug('self has data')
            self.logger.debug(self.data)
            self.uri = self.data['href']
        target = self.uri if self.uri else base_uri
        self.logger.debug('going to ' + target)
        r = self.session.get(target)
        if r.status_code == 404:
            raise InvalidPathException(target)
        if r.status_code == 403:
            raise AuthenticationException(target)
        if r.status_code == 406:
            raise PathNoLongerSupported(target)
        self.data = r.json()
        self.logger.debug('Element call got HTTP code {}'.format(r.status_code))
        return self

    def __getattr__(self, target):
        self.logger.debug('Element attrib to "{}"'.format(target))
        if not self.data:
            self()
        return APIElement(self.uri, self.data[target], self.prest)

    def __getitem__(self, index):
        # TODO needs to work like typical item accessing
        # but return an APIElement instead of a static element
        return None

    def __len__(self):
        return len(self.data)

    def find(self, **kwargs):
        # TODO iterate through list, searching nested dictionaries for key(s)
        return None

    def __repr__(self):
        return '<APIElement-{}>'.format(self.uri)

    def __str__(self):
        return str(self.data)
