import sys
import logging
import collections
import base64

import requests

from prest.errors import *


__all__ = ['Prest', 'APIElement']
base_uri = 'https://crest-tq.eveonline.com'
authed_uri = "https://crest-tq.eveonline.com/"
image_uri = "https://image.eveonline.com/"
oauth_uri = "https://login.eveonline.com/oauth"


class Prest:

    def __init__(self, version=None, **kwargs):
        self._kwargs = kwargs
        self.__configure_logger(kwargs.get('logging_level', logging.WARNING))
        self.data = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': kwargs.get('User_Agent', 'Prest v0.0.1'),
            'Accept': 'application/vnd.ccp.eve.Api-v{}+json'.format(kwargs.get('Version', 3)),
        })
        if version:
            self.session.headers.update({
                'Version': version
            })
        self.authorize_url = kwargs.get('authorize_url', None)
        self.callback_url = kwargs.get('callback_url', None)
        self.client_id = kwargs.get('client_id', None)
        self.client_secret = kwargs.get('client_secret', None)
        self.scope = kwargs.get('scope', None)
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

    def get_authorize_url(self):
        return '{}?response_type=code&redirect_uri={}&client_id={}&scope={}'.format(self.authorize_url,
            self.callback_url, self.client_id, self.scope)

    def authenticate(self, code):
        try:
            auth = base64.encodestring((self.client_id + ':' + self.client_secret).encode('ascii')).decode('utf-8')
            auth = auth.replace('\n', '').replace(' ', '')
            auth = 'Basic {}'.format(auth)
            headers = {
                'Authorization': auth
            }
            data = {
                'grant_type': 'authorization_code',
                'code': code.strip()
            }
            r = requests.post('https://login.eveonline.com/oauth/token', headers=headers, data=data)
            if not r.status_code == 200:
                raise AuthenticationFailedException('HTTP status code was {}'.format(r.status_code))
            access_token = r.json()['access_token']
            return AuthPrest(self, access_token)
        except Exception as e:
            self.logger.error('Error occurred when authenticating: ' + str(e))
            raise AuthenticationFailedException(str(e))


class AuthPrest(Prest):

    def __init__(self, prest, access_token):
        super().__init__(prest._kwargs)
        self.access_token = access_token
        self.session.headers.update({'Authorization': 'Bearer {}'.format(self.access_token)})

    def whoami(self):
        # TODO
        return None


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
            raise PathNoLongerSupportedException(target)
        if r.status_code == 40:
            raise TooManyAttemptsException(target)
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
