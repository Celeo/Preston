import sys
import logging
import collections

import requests

from prest.errors import *


__all__ = ['Prest', 'APIElement']
base_uri = 'https://crest-tq.eveonline.com'


class Prest:

    def __init__(self, version=None, **kwargs):
        self.__configure_logger(kwargs.get('logging_level', logging.WARNING))
        self.data = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': kwargs.get('User-Agent', 'Prest v0.0.1'),
            'Accept': 'application/json'
        })
        if version:
            self.session.headers.update({
                'Version': version
            })
        self()

    def __configure_logger(self, logging_level):
        self.logger = logging.getLogger('prest')
        self.logger.setLevel(logging_level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(style='{', fmt='{asctime} [{levelname}] {message}', datefmt='%Y-%m-%d %H:%M:%S'))
        handler.setLevel(logging_level)
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

    def __init__(self, uri, data, prest):
        self.uri = uri
        self.starting_data = data
        self.data = None
        self._prest = prest
        self.session = prest.session
        self.logger = prest.logger
        self.logger.debug('APIElement init: uri = "{}", starting data: {}'.format(self.uri, self.starting_data))

    def __call__(self, **kwargs):
        self.logger.debug('Element call, uri = "{}", has data: {}, has starting data: {}'.format(
            self.uri, bool(self.data), bool(self.starting_data)
        ))
        if self.data:
            self.logger.debug('Element object has data: ' + str(self.data))
            self.logger.debug(self.data)
            if not kwargs.get('overwrite_cache'):
                self.logger.debug('Not overwriting cache')
                return self
            else:
                self.logger.warning('Overwriting cache!')
                self.uri = self.data['href']
        if self.starting_data:
            self.uri = self.starting_data['href']
        target = self.uri or base_uri
        self.logger.debug('Making CREST request to: ' + target)
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
        if not self.data and not self.starting_data:
            self()
        data = self.data or self.starting_data
        if data:
            if type(data[target]) in (dict, list):
                return APIElement(self.uri, data[target], self._prest)
            else:
                return data[target]

    def __getitem__(self, index):
        data = self.data or self.starting_data
        if not isinstance(data, collections.Iterable):
            raise CRESTException('Can not get an element from a non-iterable')
        if type(data[index]) in (dict, list):
            return APIElement(self.uri, data[index], self._prest)
        else:
            return data[index]

    def __len__(self):
        return len(self.data)

    def find(self, **kwargs):
        data = self.data or self.starting_data
        if not isinstance(data, collections.Iterable):
            raise CRESTException('Can not iterate on an ' + str(type(data)))
        for element in data:
            if all(element[key] == value for key, value in kwargs.items()):
                if type(element) in (dict, list):
                    return APIElement(self.uri, element, self._prest)
                else:
                    return element
        return None

    def __repr__(self):
        return '<APIElement-{}>'.format(self.uri)

    def __str__(self):
        return str(self.data)
