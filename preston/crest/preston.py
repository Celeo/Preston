import sys
import logging
import collections
import base64
import time

import requests

from preston.crest.errors import *
from preston.crest.cache import *


base_url = 'https://crest-tq.eveonline.com/'
image_url = 'https://image.eveonline.com/'
oauth_url = 'https://login.eveonline.com/oauth/'
token_url = 'https://login.eveonline.com/oauth/token'
authorize_url = 'https://login.eveonline.com/oauth/authorize'

__all__ = ['Preston', 'AuthPreston', 'APIElement']


class Preston:

    def __init__(self, **kwargs):
        """
        This class is the base for accessing CREST. It contains the base url's
        data for building urls as CREST was deigned to do instead of using hard-
        coded urls for accessing endpoints. See README for usage information.

        Optional values from kwargs:
            loggin_level (int) - logging level to set
            client_id (str) - authenticated CREST app client id
            client_secret (str) - authenticated CREST app client secret
            callback_url (str) - authenticated CREST app callback URL
            scope (str) - authenticated CREST app scope

        Args:
            kwargs - optional parameters for configuration

        Returns:
            None
        """
        self._kwargs = kwargs
        self.__configure_logger(kwargs.get('logging_level', logging.ERROR))
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': kwargs.get('user_agent', 'Preston (github.com/Celeo/Preston)'),
            'Accept': 'application/vnd.ccp.eve.Api-v{}+json'.format(kwargs.get('Version', 3)),
        })
        self.client_id = kwargs.get('client_id', None)
        self.client_secret = kwargs.get('client_secret', None)
        self.callback_url = kwargs.get('callback_url', None)
        self.scope = kwargs.get('scope', '')
        self.cache = Cache(self, base_url)

    def __configure_logger(self, logging_level):
        """
        Configure the internal debugging logger.

        Args:
            logging_level (int) - logging level to set

        Returns:
            None
        """
        self.logger = logging.getLogger('preston.' + self.__class__.__name__)
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
                new APIElement object is returned that points to that url.
            If the element requested is a dict or list, a new APIElement
                is returned with that subset of the page's data.
            If neither of the above is true, then the data is returned as-is.
        """
        if not self.cache.check(base_url):
            self()
        self.logger.debug('Root getattr to "{}"'.format(target))
        subset = self.cache.get(base_url)[target]
        if type(subset) == dict and subset.get('href'):
            return APIElement(subset['href'], None, self)
        if type(subset) in (dict, list):
            return APIElement(base_url, subset, self)
        return subset

    def __call__(self):
        """
        Re-request the base url from CREST and store it in the cache.

        Args:
            None

        Returns:
            self
        """
        self.logger.info('Root call')
        r = self.session.get(base_url)
        if r.status_code == 404:
            raise InvalidPathException(base_url)
        if r.status_code == 403:
            raise AuthenticationException(base_url)
        if r.status_code == 406:
            raise PathNoLongerSupportedException(base_url)
        if r.status_code == 40:
            raise TooManyAttemptsException(base_url)
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
        return str(self.cache.get(base_url))

    def __repr__(self):
        """
        Returns the class name.

        Args:
            None

        Returns:
            value (str)
        """
        return '<Preston>'

    def get_authorize_url(self):
        """
        Returns the url to direct web clients to in order to authenticate against
        EVE's SSO endpoint.

        Args:
            None

        Returns:
            value (str) of the url to redirect to
        """
        return '{}?response_type=code&redirect_uri={}&client_id={}&scope={}'.format(
            authorize_url, self.callback_url, self.client_id, self.scope)

    def _build_auth_headers(self):
        """
        Build a dictionary of the authentication required for
        accessing OAuth endpoints.

        Args:
            None

        Returns:
            value (dict) with the 'Authorization' key and value
        """
        auth = base64.encodestring((self.client_id + ':' + self.client_secret).encode('latin-1')).decode('latin-1')
        auth = auth.replace('\n', '').replace(' ', '')
        auth = 'Basic {}'.format(auth)
        headers = {
            'Authorization': auth
        }
        return headers

    def authenticate(self, code):
        """
        Authenticates with CREST with the passed code from the SSO.

        Args:
            code (str) - code from the SSO login

        Returns:
            value (preston.AuthPreston) of the new CREST connection
        """
        try:
            self.logger.debug('Getting access token from auth code')
            headers = self._build_auth_headers()
            data = {
                'grant_type': 'authorization_code',
                'code': code
            }
            r = self.session.post(oauth_url + 'token', headers=headers, data=data)
            if not r.status_code == 200:
                self.logger.error('An error occurred with getting the access token')
                raise AuthenticationFailedException('HTTP status code was {}; response: {}'.format(r.status_code, r.json()))
            access_token = r.json()['access_token']
            access_expiration = r.json()['expires_in']
            self.logger.info('Successfully got the access token')
            return AuthPreston(access_token, access_expiration, self.cache, **self._kwargs)
        except CRESTException as e:
            raise e
        except Exception as e:
            self.logger.error('Error occurred when authenticating: ' + str(e))
            raise AuthenticationFailedException(str(e))

    def use_refresh_token(self, refresh_token):
        """
        Authenticates with CREST using a refresh token previously
        gotten from CREST.

        Args:
            refresh_token (str) - refresh token from CREST

        Returns:
            new authenticated (preston.AuthPreston) connection
        """
        access_token, access_expiration = self._refresh_to_access(refresh_token)
        return AuthPreston(access_token, access_expiration, self.cache, refresh_token=refresh_token, **self._kwargs)

    def _refresh_to_access(self, refresh_token):
        """
        Get an access token from a refresh token.

        Args:
            refresh_token (str) - CREST refresh token

        Returns:
            access token (str) from CREST
        """
        headers = self._build_auth_headers()
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        r = self.session.post(token_url, headers=headers, data=data)
        return r.json()['access_token'], r.json()['expires_in']


class AuthPreston(Preston):

    def __init__(self, access_token, access_expiration, cache, **kwargs):
        """
        This class is a subclass of `preston.Preston` and modifies the session
        headers to allow for authenticated calls to CREST.

        Args:
            access_token (str) - authentication token from EVE's OAuth
            cache (preston.Cache) - cache from the `preston.Preston` superclass
            kwargs - passed to `preston.Preston`'s __init__

        Returns:
            None
        """
        self.access_token = access_token
        self.access_expiration = time.time() + access_expiration
        super().__init__(**kwargs)
        self.cache = cache
        self.refresh_token = kwargs.get('refresh_token', None)
        self.session.headers.update({'Authorization': 'Bearer {}'.format(self.access_token)})
        self.logger.info('AuthPreston init complete')

    def whoami(self):
        """
        Returns the character(s) the authentication covers.

        Args:
            None

        Returns:
            value (str) of the authenticated name(s)
        """
        return self.session.get(oauth_url + 'verify').json()

    def __repr__(self):
        """
        Returns the class name.

        Args:
            None

        Returns:
            value (str)
        """
        return '<AuthPreston>'

    def _get_new_access_token(self):
        """
        Gets a new access token from CREST using the stored refresh token.

        Args:
            None

        Returns:
            None
        """
        if not self.refresh_token:
            raise AccessTokenExpiredException()
        self.access_token, self.access_expiration = self._refresh_to_access(self.refresh_token)
        self.access_expiration = time.time() + self.access_expiration

    def __getattr__(self, target):
        """
        Supplements the preston.Preston call to `__getattr__` with
        a check for the expiration of the access token. If the
        access token is expired, an attempt is made to generate
        a new one from the resfresh_token.
        """
        if time.time() > self.access_expiration:
            self._get_new_access_token()
        return super().__getattr__(target)

    def __call__(self):
        """
        Supplements the preston.Preston call to `__call__` with
        a check for the expiration of the access token. If the
        access token is expired, an attempt is made to generate
        a new one from the resfresh_token.
        """
        if time.time() > self.access_expiration:
            self._get_new_access_token()
        return super().__call__()


class APIElement:

    def __init__(self, url, data, preston):
        """
        This class expands on the __getattr__ and __call__ functionality
        of `preston.Preston` in order to navigate through CREST.

        Args:
            url (str) - url being targeted
            data (dict) - data subset from the previous __getattr__ call
            preston (preston.Preston) - super Preston instance

        Returns:
            None
        """
        self.url = url
        self.data = data
        self._preston = preston
        self.session = preston.session
        self.logger = preston.logger
        self.cache = preston.cache
        self.cache.fetch = self.__call__
        self.logger.info('APIElement init: url = "{}"'.format(url))
        if self.data is None:
            if self.cache.check(url):
                self.data = self.cache.get(url, ignore_expires=True)
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
                return APIElement(self.url, subset, self._preston)
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
                return APIElement(self.url, subset, self._preston)
            return subset
        raise IndexError

    def __call__(self):
        """
        Request the current url from CREST and store it in the cache.

        Args:
            None

        Returns:
            self
        """
        self.logger.debug('Element call, url = "{}", has data: {}'.format(self.url, bool(self.data)))
        if self.data:
            if self.data.get('href'):
                return APIElement(self.data['href'], None, self._preston)
            return APIElement(self.url, self.data, self._preston)
        if self.cache.check(self.url):
            if not self.data:
                self.data = self.cache.get(self.url, ignore_expires=True)
            return self
        self.logger.info('Making CREST request to: ' + self.url)
        r = self.session.get(self.url)
        if r.status_code == 404:
            raise InvalidPathException(self.url)
        if r.status_code == 403:
            raise AuthenticationException(self.url)
        if r.status_code == 406:
            raise PathNoLongerSupportedException(self.url)
        if r.status_code == 40:
            raise TooManyAttemptsException(self.url)
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
                    return APIElement(self.url, element, self._preston)
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
        return '<APIElement-{}>'.format(self.url)

    def __str__(self):
        """
        Returns the contents of the page from the cache.

        Args:
            None

        Returns:
            value (str) of the page contents
        """
        return str(self.data)
