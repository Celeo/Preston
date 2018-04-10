import math
import re
import time
from datetime import datetime
from typing import Optional

import requests

__all__ = ['Preston']


class Cache:

    def __init__(self):
        """Cache class.

        The cache is desgined to respect the caching rules of ESI as to
        not request a page more often than it is updated by the server.

        Args:
            None

        Returns:
            None
        """
        self.data = {}

    def _get_expiration(self, headers: dict) -> int:
        """Gets the expiration time of the data from the response headers.

        Args:
            headers: dictionary of headers from ESI

        Returns:
            value of seconds from now the data expires
        """
        expiration_str = headers.get('expires')
        if not expiration_str:
            return 0
        expiration = datetime.strptime(expiration_str, '%a, %d %b %Y %H:%M:%S %Z')
        delta = (expiration - datetime.utcnow()).total_seconds()
        return math.ceil(abs(delta))

    def set(self, response: 'requests.Response') -> None:
        """Adds a response to the cache.

        Args:
            response: response from ESI

        Returns:
            None
        """
        self.data[response.url] = SavedEndpoint(
            response.json(),
            self._get_expiration(response.headers)
        )

    def _check_expiration(self, url: 'SavedEndpoint', data: dict) -> dict:
        """Checks the expiration time for data for a url.

        If the data has expired, it is deleted from the cache.

        Args:
            url: url to check
            data: page of data for that url

        Returns:
            value of either the passed data or None if it expired
        """
        if data.expires_after < time.time():
            del self.data[url]
            data = None
        return data

    def check(self, url: str) -> Optional['SavedEndpoint']:
        """Check if data for a url has expired.

        Data is not fetched again if it has expired.

        Args:
            url (str): url to check expiration on

        Returns:
            any: value of the data, possibly None
        """
        url = self._proper_url(url)
        data = self.data.get(url)
        if data:
            data = self._check_expiration(url, data)
        return data.data if data else None


class SavedEndpoint:

    def __init__(self, data: dict, expires_in: float) -> None:
        """SavedEndpoint class.

        A wrapper around a page from ESI that also includes the expiration time
        in seconds and the time after which the wrapped data expires.

        Args:
            data: page data from ESI
            expires_in: number of seconds from now that the data expires

        Returns:
            None
        """
        self.data = data
        self.expires_in = expires_in
        self.expires_after = time.time() + expires_in


class Preston:

    BASE_URL = 'https://esi.tech.ccp.is'
    SPEC_URL = BASE_URL + '/_latest/swagger.json'
    METHODS = ['get', 'post', 'put']
    OPERATION_ID_KEY = 'operationId'
    VAR_REPLACE_REGEX = r'{(\w+)}'

    def __init__(self) -> None:
        self.spec = None

    def _get_spec(self) -> dict:
        """Returns the ESI OpenAPI spec data.

        This method caches the spec in the object.

        Args:
            None

        Returns:
            OpenAPI data
        """
        if self.spec:
            return self.spec
        self.spec = requests.get(self.SPEC_URL).json()
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
        # TODO hook up cache
        return requests.get(path).json()

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


preston = Preston()
# path = preston._path_for_opid('get_characters_character_id')
# path = preston._insert_vars(path, dict(character_id=91316135))
# print(path)

data = preston.get_op('get_characters_character_id', dict(character_id=91316135))
print(data)
