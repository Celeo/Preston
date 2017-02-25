import sys
import logging
import re
import base64
import time

import requests

from preston.esi.cache import Cache


base_url = 'https://esi.tech.ccp.is/'
oauth_url = 'https://login.eveonline.com/oauth/'
token_url = 'https://login.eveonline.com/oauth/token'
authorize_url = 'https://login.eveonline.com/oauth/authorize'

__all__ = ['Preston', 'AuthPreston', 'Page']


class Preston:

    def __init__(self, **kwargs):
        """preston.esi.preston.Preston

        This class is the base for accessing ESI. It contains the base url's
        data for building urls as ESI was deigned to do instead of using hard-
        coded urls for accessing endpoints. See README for usage information.

        Optional values from kwargs:
            loggin_level (int): logging level to set
            client_id (str): authenticated ESI app client id
            client_secret (str): authenticated ESI app client secret
            callback_url (str): authenticated ESI app callback URL
            scope (str): authenticated ESI app scope

        Args:
            kwargs (dcit): optional parameters for configuration

        Returns:
            None
        """
        self._kwargs = kwargs
        self.version = kwargs.get('version', 'latest')
        self.datasource = 'tranquility'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': kwargs.get('user_agent', 'Preston (github.com/Celeo/Preston)'),
            'Accept': 'application/json'
        })
        self.client_id = kwargs.get('client_id', None)
        self.client_secret = kwargs.get('client_secret', None)
        self.callback_url = kwargs.get('callback_url', None)
        self.scope = kwargs.get('scope', '')
        self.__configure_logger(kwargs.get('logging_level', logging.ERROR))
        self.cache = Cache(self, base_url)

    def __configure_logger(self, logging_level):
        """Configure the internal debugging logger

        Args:
            logging_level (int): logging level to set

        Returns:
            None
        """
        self.logger = logging.getLogger('preston.' + self.__class__.__name__)
        self.logger.setLevel(logging_level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(style='{', fmt='{asctime} [{levelname}] {message}', datefmt='%Y-%m-%d %H:%M:%S'))
        handler.setLevel(logging_level)
        self.logger.addHandler(handler)

    def __getattr__(self, attr):
        """Build a URL to query.

        Args:
            attr (str): first endpoint component OR
                version string to set

        Returns:
            preston.esi.preston.Page: new Page object if
                the version-setting function wasn't used, otherwise
                this same object with the version set
        """
        if re.match(r'(v\d+|latest|dev|legacy)', attr):
            self.version = attr
            return self
        return Page(self, attr)

    def __str__(self):
        """Return a string representation of the object.

        Args:
            None

        Returns:
            str: string representation
        """
        return '<preston.esi.preston.Preston>'

    def get_authorize_url(self):
        """Get authorize URL for the SSO.

        Returns the url to direct web clients to in order to authenticate against
        EVE's SSO endpoint.

        Args:
            None

        Returns:
            str: the url to redirect to
        """
        return '{}?response_type=code&redirect_uri={}&client_id={}&scope={}'.format(
            authorize_url, self.callback_url, self.client_id, self.scope)

    def _build_auth_headers(self):
        """Create authentication headers.

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
        """Authenticates with CREST with the passed code from the SSO.

        Args:
            code (str): code from the SSO login

        Returns:
            preston.esi.preston.AuthPreston: new root object
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
                raise Exception('HTTP status code was {}; response: {}'.format(r.status_code, r.json()))
            access_token = r.json()['access_token']
            access_expiration = r.json()['expires_in']
            refresh_token = r.json()['refresh_token']
            self.logger.info('Successfully got the access token')
            return AuthPreston(access_token, access_expiration, self, refresh_token)
        except Exception as e:
            raise e
        except Exception as e:
            self.logger.error('Error occurred when authenticating: ' + str(e))
            raise Exception(str(e))

    def use_refresh_token(self, refresh_token):
        """Use a refersh token to authenticate.

        Authenticates with ESI using a refresh token previously
        gotten from ESI.

        Args:
            refresh_token (str): refresh token from ESI

        Returns:
            preston.esi.preston.AuthPreston: new root object
        """
        access_token, access_expiration = self._refresh_to_access(refresh_token)
        return AuthPreston(access_token, access_expiration, self, refresh_token)

    def _refresh_to_access(self, refresh_token):
        """Get an access token from a refresh token.

        Args:
            refresh_token (str) - ESI refresh token

        Returns:
            str: access token from ESI
        """
        headers = self._build_auth_headers()
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        r = self.session.post(token_url, headers=headers, data=data)
        return r.json()['access_token'], r.json()['expires_in']


class AuthPreston(Preston):

    def __init__(self, access_token, access_expiration, base, refresh_token=None):
        """Authenticated ESI access class.

        This class is a subclass of `preston.esi.preston.Preston` and modifies the session
        headers to allow for authenticated calls to ESI.

        Args:
            access_token (str): authentication token from EVE's OAuth
            cache (preston.Cache): cache from the `preston.esi.preston.Preston` superclass
            kwargs (dict): passed to `preston.esi.preston.Preston`'s __init__
        """
        self.access_token = access_token
        self.access_expiration = time.time() + access_expiration
        super().__init__(**base._kwargs)
        self.cache = base.cache
        self.refresh_token = refresh_token
        self.session.headers.update({'Authorization': 'Bearer {}'.format(self.access_token)})
        self.logger.info('AuthPreston init complete')

    def whoami(self):
        """Returns the character(s) the authentication covers.

        Args:
            None

        Returns:
            str: authenticated character's name
        """
        return self.session.get(oauth_url + 'verify').json()

    def __str__(self):
        """Return a string representation of the object.

        Args:
            None

        Returns:
            str: string representation
        """
        return '<preston.esi.preston.AuthPreston>'

    def _get_new_access_token(self):
        """Gets a new access token from CREST using the stored refresh token.

        Args:
            None

        Returns:
            None
        """
        if not self.refresh_token:
            raise Exception('Expired token')
        self.access_token, self.access_expiration = self._refresh_to_access(self.refresh_token)
        self.access_expiration = time.time() + self.access_expiration

    def __getattr__(self, attr):
        """Build a URL to query.

        Supplements the preston.esi.preston.Preston call to
        `__getattr__` with a check for the expiration of the
        access token. If the access token is expired, an attempt
        is made to generate a new one from the resfresh_token.

        Args:
            attr (str): first endpoint component OR
                version string to set

        Returns:
            preston.esi.preston.Page: new Page object if
                the version-setting function wasn't used, otherwise
                this same object with the version set
        """
        if time.time() > self.access_expiration:
            self._get_new_access_token()
        return super().__getattr__(attr)


class Page:

    def __init__(self, base, endpoint):
        """Object representing a page on ESI

        Args:
            base (preston.esi.preston.Preston or preston.esi.preston.Page): base object
            endpoint (str): which endpoint (or piece) the code is building
        """
        self._base = base
        self.cache = base.cache
        self.logger = base.logger
        self.version = base.version
        self.datasource = base.datasource
        self.session = base.session
        self.endpoint = endpoint

    def __getattr__(self, attr):
        """Build a URL to query.

        Args:
            attr (str): next endpoint component

        Returns:
            preston.esi.preston.Page: new Page object with next endpoint component
        """
        return Page(self._base, self.endpoint + '/' + str(attr))

    def __getitem__(self, key):
        """Build a URL to query.

        While the __getattr__ syntax is cleaner and less typing, this method is
        available for endpoints that require variables to be set in the middle of
        the URL that are numbers, like '/corporations/{corporation_id}/members'.
        In this instance, `preston.corporations.100000.members()` is invalid Python,
        and thus this method allows the user to do `preston.corporations['100000'].members()

        Args:
            key (any): next endpoint component

        Returns:
            preston.esi.preston.Page: new Page object with next endpoint component
        """
        return Page(self._base, self.endpoint + '/' + str(key))

    def __call__(self, value=None, **kwargs):
        """Fetch the ESI page.

        This endpoint requires that the endpoint string be complete
        and all needed arguments be passed this this method. The optional
        single `value` parameter is for endpoints like /universe/types/{type_id}/
        where a variable is inside the URL.

        Args:
            value (optional, any): value to append

        Returns:
            dict: json data from ESI
        """
        url = (
            base_url +
            self.version +
            '/' + self.endpoint +
            ('/{}/'.format(value) if value else '/') +
            '?' + '&'.join(
                ['{}={}'.format(key, value) for key, value in kwargs.items()]
            )
        )
        cached = self.cache.check(url)
        if cached:
            self.logger.debug('Data was cached - returning from cache')
            return cached
        self.logger.debug('GETting ' + url)
        r = self.session.get(url, allow_redirects=True)
        self.cache.set(r)
        return r.json()

    def __str__(self):
        """Return a string representation of the object.

        Args:
            None

        Returns:
            str: string representation
        """
        return '<preston.esi.preston.Page: {}>'.format(self.endpoint)
