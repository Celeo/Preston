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

    def __init__(self, **kwargs):
        """
        This class is the base for accessing CREST. It contains the base URI's
        data for building URIs as CREST was deigned to do instead of using hard-
        coded URIs for accessing endpoints. See README for usage information.

        Optional values from kwargs:
            loggin_level (int) - logging level to set

        Args:
            kwargs - optional parameters for configuration

        Returns:
            None
        """
        self._kwargs = kwargs
        self.__configure_logger(kwargs.get('logging_level', logging.ERROR))
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': kwargs.get('User_Agent', 'Prest v'), # TODO version
            'Accept': 'application/vnd.ccp.eve.Api-v{}+json'.format(kwargs.get('Version', 3)),
        })
        self.client_id = kwargs.get('client_id', None)
        self.client_secret = kwargs.get('client_secret', None)
        self.callback_url = kwargs.get('callback_url', None)
        self.scope = kwargs.get('scope', None)
        self.cache = Cache(self, base_uri)
        self()

    def __configure_logger(self, logging_level):
        """
        Configure the internal debugging logger.

        Args:
            logging_level (int) - logging level to set

        Returns:
            None
        """
        self.logger = logging.getLogger('prest.' + self.__class__.__name__)
        self.logger.setLevel(logging_level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(style='{', fmt='{asctime} [{levelname}] {message}', datefmt='%Y-%m-%d %H:%M:%S'))
        handler.setLevel(logging_level)
        self.logger.addHandler(handler)

    @property
    def version(self):
        """
        Return the version of CREST being requested.

        Args:
            None

        Returns:
            value (int) of the CREST version being requested
        """
        return self.session.headers.get('Version')

    @version.setter
    def version(self, value):
        """
        Sets the version of CREST to request.

        Args:
            value (str) - version to request

        Returns:
            None
        """
        self.session.headers.update({
            'Version': version
        })

    def __getattr__(self, target):
        """
        Get an element from the current page.

        Args:
            target (str) - dictionary element to retrieve

        Returns:
            If the element requested is a dict with a herf key, a
                new APIElement object is returned that points to that URI.
            If the element requested is a dict or list, a new APIElement
                is returned with that subset of the page's data.
            If neither of the above is true, then the data is returned as-is.
        """
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
        """
        Re-request the base URI from CREST and store it in the cache.

        Args:
            None

        Returns:
            self
        """
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
        """
        Returns the contents of the page from the cache.

        Args:
            None

        Returns:
            value (str) of the page contents
        """
        return str(self.cache.get(base_uri))

    def __repr__(self):
        """
        Returns the class name.

        Args:
            None

        Returns:
            value (str)
        """
        return '<Prest>'

    def get_authorize_url(self):
        """
        Returns the URI to direct web clients to in order to authenticate against
        EVE's SSO endpoint.

        Args:
            None

        Returns:
            value (str) of the URI to redirect to
        """
        return '{}?response_type=code&redirect_uri={}&client_id={}&scope={}'.format(
            self.authorize_url, self.callback_url, self.client_id, self.scope)

    def authenticate(self, code):
        """
        Authenticates with CREST with the passed code from the SSO.

        Args:
            code (str) - code from the SSO login

        Returns:
            value (prest.AuthPrest) of the new CREST connection
        """
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
        """
        This class is a subclass of `prest.Prest` and modifies the session
        headers to allow for authenticated calls to CREST.

        Args:
            access_token (str) - authentication token from EVE's OAuth
            cache (prest.Cache) - cache from the `prest.Prest` superclass
            kwargs - passed to `prest.Prest`'s __init__

        Returns:
            None
        """
        super().__init__(**kwargs)
        self.access_token = access_token
        self.cache = cache
        self.session.headers.update({'Authorization': 'Bearer {}'.format(self.access_token)})
        self.logger.info('AuthPrest init complete')

    def whoami(self):
        """
        Returns the character(s) the authentication covers.

        Args:
            None

        Returns:
            value (str) of the authenticated name(s)
        """
        return self.session.get(oauth_uri + 'verify').json()

    def __repr__(self):
        """
        Returns the class name.

        Args:
            None

        Returns:
            value (str)
        """
        return '<AuthPrest>'


class APIElement:

    def __init__(self, uri, data, prest):
        """
        This class expands on the __getattr__ and __call__ functionality
        of `prest.Prest` in order to navigate through CREST.

        Args:
            uri (str) - URI being targeted
            data (dict) - data subset from the previous __getattr__ call
            prest (prest.Prest) - super Prest instance

        Returns:
            None
        """
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
        """
        Get an element from the current page.

        Args:
            target (str) - dictionary element to retrieve

        Returns:
            If the element requested is a dict or list, a new APIElement
                is returned with that subset of the page's data.
            If neither of the above is true, then the data is returned as-is.
        """
        self.logger.debug('Element getattr to "{}"'.format(target))
        if self.data:
            subset = self.data[target]
            if type(subset) in (dict, list):
                return APIElement(self.uri, subset, self._prest)
            return subset

    def __getitem__(self, index):
        """
        Get an element from the current page.

        Args:
            index (int) - list index to retrieve

        Returns:
            If the element requested is a dict or list, a new APIElement
                is returned with that subset of the page's data.
            If neither of the above is true, then the data is returned as-is.
        """
        self.logger.debug('Element getitem to "{}"'.format(index))
        if self.data:
            subset = self.data[index]
            if type(self.data[index]) in (dict, list):
                return APIElement(self.uri, subset, self._prest)
            return subset

    def __call__(self):
        """
        Request the current URI from CREST and store it in the cache.

        Args:
            None

        Returns:
            self
        """
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
        """
        Returns the number of items in the stored data.

        More of a debugging tool, since getting the number of dictionary keys
        isn't a good indicator of how much data is actually here.

        Args:
            None

        Returns:
            value (int) of the number of keys in the data
        """
        return len(self.data)

    def find(self, **kwargs):
        """
        A helper method for navigating lists of dicts on the page.

        The kwargs parameter is used to pass requirements for matching the nested
        dictionary keys. All key-values must match.

        Args:
            kwargs - matching requirements

        Returns:
            An APIElement matching the filter or None if nothing matched
        """
        if not isinstance(self.data, collections.Iterable):
            raise CRESTException('Can not iterate on an ' + str(type(self.data)))
        for element in self.data:
            if all(element[key] == value for key, value in kwargs.items()):
                if type(element) in (dict, list):
                    return APIElement(self.uri, element, self._prest)
                return element
        return None

    def __repr__(self):
        """
        Returns the class name.

        Args:
            None

        Returns:
            value (str)
        """
        return '<APIElement-{}>'.format(self.uri)

    def __str__(self):
        """
        Returns the contents of the page from the cache.

        Args:
            None

        Returns:
            value (str) of the page contents
        """
        return str(self.data)
