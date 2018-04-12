import base64
import re
import time
from typing import Optional, Tuple

import requests

from .cache import Cache


class Preston:

    BASE_URL = 'https://esi.tech.ccp.is'
    SPEC_URL = BASE_URL + '/_{}/swagger.json'
    OAUTH_URL = 'https://login.eveonline.com/oauth/'
    TOKEN_URL = OAUTH_URL + 'oauth/token'
    AUTHORIZE_URL = OAUTH_URL + 'oauth/authorize'
    METHODS = ['get', 'post', 'put', 'delete']
    OPERATION_ID_KEY = 'operationId'
    VAR_REPLACE_REGEX = r'{(\w+)}'

    def __init__(self, **kwargs: str) -> None:
        self.cache = Cache()
        self.spec = None
        self.version = kwargs.get('version', 'latest')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': kwargs.get('user_agent', 'Preston (github.com/Celeo/Preston)'),
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
        self._try_refresh_access_token()
        self._update_access_token_header()

    def _get_access_from_refresh(self) -> Tuple[str, float]:
        headers = self._build_auth_headers()
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }
        r = self.session.post(self.TOKEN_URL, headers=headers, data=data)
        return (r.json()['access_token'], r.json()['expires_in'])

    def _build_auth_headers(self) -> dict:
        auth = base64.encodestring((self.client_id + ':' + self.client_secret).encode('latin-1')).decode('latin-1')
        auth = auth.replace('\n', '').replace(' ', '')
        auth = 'Basic {}'.format(auth)
        headers = {'Authorization': auth}
        return headers

    def _get_spec(self) -> dict:
        if self.spec:
            return self.spec
        self.spec = requests.get(self.SPEC_URL.format(self.version)).json()
        return self.spec

    def _get_path_for_op_id(self, id: str) -> Optional[str]:
        for path_key, path_value in self._get_spec()['paths'].items():
            for method in self.METHODS:
                if method in path_value:
                    if self.OPERATION_ID_KEY in path_value[method]:
                        if path_value[method][self.OPERATION_ID_KEY] == id:
                            return path_key
        return None

    def _try_refresh_access_token(self) -> None:
        if not self.access_token:
            return
        if not self._is_access_token_expired():
            return
        if not self.refresh_token:
            raise Exception('Access token is expired and there is no stored refresh token')
        self.access_token, self.access_expiration = self.get_access_from_refresh(self.refresh_token)

    def _is_access_token_expired(self) -> bool:
        return time.time() > self.access_expiration

    def get_authorize_url(self) -> str:
        return (
            f'{self.AUTHORIZE_URL}?response_type=code&redirect_uri={self.callback_url}'
            f'&client_id={self.client_id}&scope={self.scope}'
        )

    def authenticate(self, code: str) -> 'Preston':
        # TODO
        pass

    def _update_access_token_header(self) -> None:
        if self.access_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}'
            })

    def _insert_vars(self, path: str, data: dict) -> str:
        while True:
            match = re.search(self.VAR_REPLACE_REGEX, path)
            if not match:
                return path
            replace_from = match.group(0)
            replace_with = str(data[match.group(1)])
            path = path.replace(replace_from, replace_with)

    def get_path(self, path: str, data: dict) -> dict:
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
        path = self._get_path_for_op_id(id)
        return self.get_path(path, kwargs)
