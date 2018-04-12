import base64
import re
import time
from typing import Optional, Tuple

import requests

from .cache import Cache


class Preston:
    """Preston class.

    This class is used to interface with the EVE Online "ESI" API.

    The __init__ method only **kwargs instead of a specific
    listing of arguments; here's the list of useful key-values:

        version                 version of the spec to load

        user_agent              user-agent to use

        client_id               app's client id

        client_secret           app's client secret

        callback_url            app's callback url

        scope                   app's scope(s)

        access_token            if supplied along with access_expiration,
                                Preston will make authenticated calls to ESI

        access_expiration       see above

        refresh_token           if supplied, Preston will use it to get new
                                access tokens; can be supplied with or without
                                access_token and access_expiration

    Args:
        kwargs: various configuration options
    """
    BASE_URL = 'https://esi.tech.ccp.is'
    SPEC_URL = BASE_URL + '/_{}/swagger.json'
    OAUTH_URL = 'https://login.eveonline.com/oauth/'
    TOKEN_URL = OAUTH_URL + 'token'
    AUTHORIZE_URL = OAUTH_URL + 'authorize'
    WHOAMI_URL = OAUTH_URL + 'verify'
    METHODS = ['get', 'post', 'put', 'delete']
    OPERATION_ID_KEY = 'operationId'
    VAR_REPLACE_REGEX = r'{(\w+)}'

    def __init__(self, **kwargs: str) -> None:
        self.cache = Cache()
        self.spec = None
        self.version = kwargs.get('version', 'latest')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': kwargs.get('user_agent', ''),
            'Accept': 'application/json'
        })
        self.client_id = kwargs.get('client_id')
        self.client_secret = kwargs.get('client_secret')
        self.callback_url = kwargs.get('callback_url')
        self.scope = kwargs.get('scope', '')
        self.access_token = kwargs.get('access_token')
        self.access_expiration = kwargs.get('access_expiration')
        self.refresh_token = kwargs.get('refresh_token')
        self._kwargs = kwargs
        if not kwargs.get('no_update_token', False):
            self._try_refresh_access_token()
            self._update_access_token_header()

    def copy(self) -> 'Preston':
        """Creates a copy of this Preston object.

        The returned instance is not connected to this, so you can set
        whichever headers or other data you want without impacting this instance.

        The configuration of the returned instance will match the (original)
        configuration of this instance - the kwargs are reused.

        Args:
            None

        Returns:
            new Preston instance
        """
        return Preston(**self._kwargs)

    def _get_access_from_refresh(self) -> Tuple[str, float]:
        """Uses the stored refresh token to get a new access token.

        This method assumes that the refresh token exists.

        Args:
            None

        Returns:
            new access token and expiration time (from now)
        """
        headers = self._get_authorization_headers()
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }
        r = self.session.post(self.TOKEN_URL, headers=headers, data=data)
        response_data = r.json()
        return (response_data['access_token'], response_data['expires_in'])

    def _get_authorization_headers(self) -> dict:
        """Constructs and returns the Authorization header for the client app.

        Args:
            None

        Returns:
            header dict for communicating with the authorization endpoints
        """
        auth = base64.encodestring((self.client_id + ':' + self.client_secret).encode('latin-1')).decode('latin-1')
        auth = auth.replace('\n', '').replace(' ', '')
        auth = 'Basic {}'.format(auth)
        headers = {'Authorization': auth}
        return headers

    def _get_spec(self) -> dict:
        """Fetches the OpenAPI spec from the server.

        If the spec has already been fetched, the cached version is returned instead.

        ArgS:
            None

        Returns:
            OpenAPI spec data
        """
        if self.spec:
            return self.spec
        self.spec = requests.get(self.SPEC_URL.format(self.version)).json()
        return self.spec

    def _get_path_for_op_id(self, id: str) -> Optional[str]:
        """Searches the spec for a path matching the operation id.

        Args:
            id: operation id

        Returns:
            path to the endpoint, or None if not found
        """
        for path_key, path_value in self._get_spec()['paths'].items():
            for method in self.METHODS:
                if method in path_value:
                    if self.OPERATION_ID_KEY in path_value[method]:
                        if path_value[method][self.OPERATION_ID_KEY] == id:
                            return path_key
        return None

    def _try_refresh_access_token(self) -> None:
        """Attempts to get a new access token using the refresh token, if needed.

        If the access token is expired and this instance has a stored refresh token,
        then the refresh token is in the API call to get a new access token. If
        successful, this instance is modified in-place with that new access token.

        Args:
            None

        Returns:
            None
        """
        if not self.access_token:
            return
        if not self._is_access_token_expired():
            return
        if not self.refresh_token:
            raise Exception('Access token is expired and there is no stored refresh token')
        self.access_token, self.access_expiration = self._get_access_from_refresh()
        self.access_expiration = time.time() + self.access_expiration

    def _is_access_token_expired(self) -> bool:
        """Returns true if the stored access token has expired.

        Args:
            None

        Returns:
            True if the access token is expired
        """
        return time.time() > self.access_expiration

    def get_authorize_url(self) -> str:
        """Constructs and returns the authorization URL.

        This is the URL that a user will have to navigate to in their browser
        and complete the login and authorization flow. Upon completion, they
        will be redirected to your app's callback URL.

        Args:
            None

        Returns:
            URL
        """
        return (
            f'{self.AUTHORIZE_URL}?response_type=code&redirect_uri={self.callback_url}'
            f'&client_id={self.client_id}&scope={self.scope}'
        )

    def authenticate(self, code: str) -> 'Preston':
        """Authenticates using the code from the EVE SSO.

        A new Preston object is returned; this object is not modified.

        The intended usage is:

            auth = preston.authenticate('some_code_here')

        Args:
            code: SSO code

        Returns:
            new Preston, authenticated
        """
        headers = self._get_authorization_headers()
        data = {
            'grant_type': 'authorization_code',
            'code': code
        }
        r = self.session.post(self.TOKEN_URL, headers=headers, data=data)
        if not r.status_code == 200:
            raise Exception(f'Could not authenticate, got repsonse code {r.status_code}')
        new_kwargs = dict(self._kwargs)
        response_data = r.json()
        new_kwargs['access_token'] = response_data['access_token']
        new_kwargs['access_expiration'] = time.time() + float(response_data['expires_in'])
        new_kwargs['refresh_token'] = response_data['refresh_token']
        return Preston(**new_kwargs)

    def _update_access_token_header(self) -> None:
        """Updates the requests session with the access token header.

        This method does nothing if this instance does not have a
        stored access token.

        Args:
            None

        Returns:
            None
        """
        if self.access_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}'
            })

    def _insert_vars(self, path: str, data: dict) -> str:
        """Inserts variables into the ESI URL path.

        Args:
            path: raw ESI URL path
            data: data to insert into the URL

        Returns:
            path with variables filled
        """
        while True:
            match = re.search(self.VAR_REPLACE_REGEX, path)
            if not match:
                return path
            replace_from = match.group(0)
            replace_with = str(data[match.group(1)])
            path = path.replace(replace_from, replace_with)

    def whoami(self) -> dict:
        """Returns the basic information about the authenticated character.

        Obviously doesn't do anything if this Preston instance is not
        authenticated, so it returns an empty dict.

        Args:
            None

        Returns:
            character info if authenticated, otherwise an empty dict
        """
        if not self.access_token:
            return {}
        self._try_refresh_access_token()
        return self.session.get(self.WHOAMI_URL).json()

    def get_path(self, path: str, data: dict) -> dict:
        """Queries the ESI by an endpoint URL.

        This method is not marked "private" as it _can_ be used
        by consuming code, but it's probably easier to call the
        `get_op` method instead.

        Args:
            path: raw ESI URL path
            data: data to insert into the URL

        Returns:
            ESI data
        """
        path = self._insert_vars(path, data)
        path = self.BASE_URL + path
        data = self.cache.check(path)
        if data:
            return data
        self._try_refresh_access_token()
        r = self.session.get(path)
        self.cache.set(r)
        return r.json()

    def get_op(self, id: str, **kwargs: str) -> dict:
        """Queries the ESI by looking up an operation id.

        Args:
            id: operation id
            kwargs: data to populate the endpoint's URL variables

        Returns:
            ESI data
        """
        path = self._get_path_for_op_id(id)
        return self.get_path(path, kwargs)
