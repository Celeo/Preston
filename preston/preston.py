import base64
import logging
import re
import sys
from typing import Optional

import requests

from .cache import Cache


class Preston:

    BASE_URL = 'https://esi.tech.ccp.is'
    SPEC_URL = BASE_URL + '/_{}/swagger.json'
    OAUTH_URL = 'https://login.eveonline.com/oauth/'
    TOKEN_URL = 'https://login.eveonline.com/oauth/token'
    AUTHORIZE_URL = 'https://login.eveonline.com/oauth/authorize'
    METHODS = ['get', 'post', 'put']
    OPERATION_ID_KEY = 'operationId'
    VAR_REPLACE_REGEX = r'{(\w+)}'

    def __init__(self, **kwargs: dict) -> None:
        """Preston class.

        Interface for accessing the ESI.

        Args:
            kwargs: optional parameters for configuration

        Returns:
            None
        """
        self.cache = Cache()
        self.spec = None
        self.version = kwargs.get('version', 'latest')
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

    def __configure_logger(self, logging_level: int) -> None:
        """Configure the internal debugging logger.

        Args:
            logging_level: logging level to set

        Returns:
            None
        """
        self.logger = logging.getLogger('preston.' + self.__class__.__name__)
        self.logger.setLevel(logging_level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(style='{', fmt='{asctime} [{levelname}] {message}', datefmt='%Y-%m-%d %H:%M:%S'))
        handler.setLevel(logging_level)
        self.logger.addHandler(handler)

    def get_authorize_url(self) -> str:
        """Get authorize URL for the SSO.

        Returns the url to direct web clients to in order to authenticate against
        EVE's SSO endpoint.

        Args:
            None

        Returns:
           the URL to redirect to
        """
        return '{}?response_type=code&redirect_uri={}&client_id={}&scope={}'.format(
            self.AUTHORIZE_URL, self.callback_url, self.client_id, self.scope)

    def _build_auth_headers(self):
        """Create authentication headers.

        Build a dictionary of the authentication required for
        accessing OAuth endpoints.

        Args:
            None

        Returns:
            value with the 'Authorization' key and value
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
            code: code from the SSO login

        Returns:
            new root object
        """
        try:
            self.logger.debug('Getting access token from auth code')
            headers = self._build_auth_headers()
            data = {
                'grant_type': 'authorization_code',
                'code': code
            }
            r = self.session.post(self.OAUTH_URL + 'token', headers=headers, data=data)
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
            refresh_token: refresh token from ESI

        Returns:
            preston.esi.preston.AuthPreston: new root object
        """
        access_token, access_expiration = self._refresh_to_access(refresh_token)
        return AuthPreston(access_token, access_expiration, self, refresh_token)

    def use_saved(self, refresh_token, access_token, access_expiration):
        """Use saved tokens and expiration, e.g. when you need get info for multiple characters in loop

        Args:
            refresh_token (str): refresh token from ESI
            access_token (str): authentication token from EVE's OAuth
            access_expiration (str): expiration date from EVE's OAuth

        Returns:
            auth
        """
        auth = AuthPreston(access_token, 0, self, refresh_token)
        auth.access_expiration = access_expiration
        return auth

    def _refresh_to_access(self, refresh_token):
        """Get an access token from a refresh token.

        Args:
            refresh_token - ESI refresh token

        Returns:
            access token from ESI
        """
        headers = self._build_auth_headers()
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        r = self.session.post(token_url, headers=headers, data=data)
        return r.json()['access_token'], r.json()['expires_in']

    def _get_spec(self) -> dict:
        """Returns the ESI OpenAPI spec data.

        This method caches the spec in this object.

        Args:
            None

        Returns:
            OpenAPI spec data
        """
        if self.spec:
            return self.spec
        self.spec = requests.get(self.SPEC_URL.format(self.version)).json()
        return self.spec

    def _path_for_opid(self, id: str) -> Optional[str]:
        """Returns the URL path for the operationId.

        Args:
            id: ESI operationId

        Returns:
            URL path, or None if not found
        """
        for path_key, path_value in self._get_spec()['paths'].items():
            for method in self.METHODS:
                if method in path_value:
                    if self.OPERATION_ID_KEY in path_value[method]:
                        if path_value[method][self.OPERATION_ID_KEY] == id:
                            return path_key
        return None

    def _insert_vars(self, path: str, data: dict) -> str:
        """Insert variables into URL parameters.

        Args:
            path: path to endpoint
            data: data to replace URL parameters

        Returns:
            new path
        """
        while True:
            match = re.search(self.VAR_REPLACE_REGEX, path)
            if not match:
                return path
            replace_from = match.group(0)
            replace_with = str(data[match.group(1)])
            path = path.replace(replace_from, replace_with)

    def get_path(self, path: str, data: dict=None) -> dict:
        """Get data at an ESI path.

        If you already know the URL path for an endpoint that you want to access,
        call this method with that path, optionally supplying data that is used
        to supply URL parameters.

        Args:
            path: path to endpoint
            data: optional data to replace URL parameters

        Returns:
            data from ESI
        """
        data = data or {}
        path = self._insert_vars(path, data)
        path = self.BASE_URL + path
        data = self.cache.check(path)
        if data:
            return data.data
        r = requests.get(path)
        self.cache.set(r)
        return r.json()

    def get_op(self, id: str, data: dict=None) -> dict:
        """Get data for an ESI operationId.

        This is the method to call if you want Preston to handle fetching the
        URL path for the endpoint matching the supplied operationId.

        Args:
            id: ESI operationId
            data: operation data to replace URL parameters, once determined

        Returns:
            data from ESI
        """
        path = self._path_for_opid(id)
        return self.get_path(path, data)
