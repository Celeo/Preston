import sys
import logging
import collections
import base64

import requests

from prest.errors import *
from prest.cache import *


__all__ = ['Prest', 'AuthPrest', 'APIElement']
base_uri = 'https://crest-tq.eveonline.com/'
image_uri = 'https://image.eveonline.com/'
oauth_uri = 'https://login.eveonline.com/oauth/'


class Prest:

    def __init__(self, version=None, **kwargs):
        self._kwargs = kwargs
        self.__configure_logger(kwargs.get('logging_level', logging.WARNING))
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': kwargs.get('User_Agent', 'Prest v0.0.1'),
            'Accept': 'application/vnd.ccp.eve.Api-v{}+json'.format(kwargs.get('Version', 3)),
        })
        if version:
            self.session.headers.update({
                'Version': version
            })
        self.client_id = kwargs.get('client_id', None)
        self.client_secret = kwargs.get('client_secret', None)
        self.callback_url = kwargs.get('callback_url', None)
        self.scope = kwargs.get('scope', None)
        self.cache = Cache(self, base_uri)
        self()

    def __configure_logger(self, logging_level):
        self.logger = logging.getLogger('prest.' + self.__class__.__name__)
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
        if not self.cache.check(base_uri):
            self()
        self.logger.debug('Root getattr to "{}"'.format(target))
        subset = self.cache.get(base_uri)[target]
        if type(subset) == dict and subset.get('href'):
            return APIElement(subset['href'], None, self)
        if type(subset) in (dict, list):
            return APIElement(base_uri, subset, self)
        return subset

    def __call__(self):
        self.logger.info('Root call')
        r = self.session.get(base_uri)
        if r.status_code == 404:
            raise InvalidPathException(base_uri)
        if r.status_code == 403:
            raise AuthenticationException(base_uri)
        if r.status_code == 406:
            raise PathNoLongerSupportedException(base_uri)
        if r.status_code == 40:
            raise TooManyAttemptsException(base_uri)
        self.cache.set(r)
        return self

    def __str__(self):
        return str(self.cache.get(base_uri))

    def __repr__(self):
        return '<Prest-{}>'.format(self.path)

    def get_authorize_url(self):
        return '{}?response_type=code&redirect_uri={}&client_id={}&scope={}'.format(
            self.authorize_url, self.callback_url, self.client_id, self.scope)

    def authenticate(self, code):
        try:
            self.logger.debug('Getting access token from auth code')
            auth = base64.encodestring((self.client_id + ':' + self.client_secret).encode('latin-1')).decode('latin-1')
            auth = auth.replace('\n', '').replace(' ', '')
            auth = 'Basic {}'.format(auth)
            headers = {
                'Authorization': auth
            }
            data = {
                'grant_type': 'authorization_code',
                'code': code
            }
            r = self.session.post(oauth_uri + 'token', headers=headers, data=data)
            if not r.status_code == 200:
                self.logger.error('An error occurred with getting the access token')
                raise AuthenticationFailedException('HTTP status code was {}; response: {}'.format(r.status_code, r.json()))
            access_token = r.json()['access_token']
            self.logger.info('Successfully got the access token')
            return AuthPrest(access_token, self.cache, self._kwargs)
        except CRESTException as e:
            raise e
        except Exception as e:
            self.logger.error('Error occurred when authenticating: ' + str(e))
            raise AuthenticationFailedException(str(e))


class AuthPrest(Prest):

    def __init__(self, access_token, cache, **kwargs):
        super().__init__(**kwargs)
        self.access_token = access_token
        self.cache = cache
        self.session.headers.update({'Authorization': 'Bearer {}'.format(self.access_token)})
        self.logger.info('AuthPrest init complete')

    def whoami(self):
        return self.session.get(oauth_uri + 'verify').json()

    def __repr__(self):
        return '<AuthPrest-{}'.format(self.path)


class APIElement:

    def __init__(self, uri, data, prest):
        self.uri = uri
        self.data = data
        self._prest = prest
        self.session = prest.session
        self.logger = prest.logger
        self.cache = prest.cache
        self.cache.fetch = self.__call__
        self.logger.info('APIElement init: uri = "{}"'.format(uri))
        if not self.data:
            if self.cache.check(uri):
                self.data = self.cache.get(uri, ignore_expires=True)
            else:
                self()

    def __getattr__(self, target):
        self.logger.debug('Element getattr to "{}"'.format(target))
        if self.data:
            subset = self.data[target]
            if type(subset) in (dict, list):
                return APIElement(self.uri, subset, self._prest)
            return subset

    def __getitem__(self, index):
        self.logger.debug('Element getitem to "{}"'.format(index))
        if self.data:
            subset = self.data[index]
            if type(self.data[index]) in (dict, list):
                return APIElement(self.uri, subset, self._prest)
            return subset

    def __call__(self, **kwargs):
        self.logger.debug('Element call, uri = "{}", has data: {}'.format(self.uri, bool(self.data)))
        if self.data:
            if self.data.get('href'):
                return APIElement(self.data['href'], None, self._prest)
            return APIElement(self.uri, self.data, self._prest)
        if self.cache.check(self.uri):
            if not self.data:
                self.data = self.cache.get(self.uri, ignore_expires=True)
            return self
        self.logger.info('Making CREST request to: ' + self.uri)
        r = self.session.get(self.uri)
        if r.status_code == 404:
            raise InvalidPathException(self.uri)
        if r.status_code == 403:
            raise AuthenticationException(self.uri)
        if r.status_code == 406:
            raise PathNoLongerSupportedException(self.uri)
        if r.status_code == 40:
            raise TooManyAttemptsException(self.uri)
        self.logger.debug('Element call got HTTP code {}'.format(r.status_code))
        self.cache.set(r)
        self.data = r.json()
        return self

    def __len__(self):
        return len(self.data)

    def find(self, **kwargs):
        if not isinstance(self.data, collections.Iterable):
            raise CRESTException('Can not iterate on an ' + str(type(self.data)))
        for element in self.data:
            if all(element[key] == value for key, value in kwargs.items()):
                if type(element) in (dict, list):
                    return APIElement(self.uri, element, self._prest)
                return element
        return None

    def __repr__(self):
        return '<APIElement-{}>'.format(self.uri)

    def __str__(self):
        return str(self.data)
