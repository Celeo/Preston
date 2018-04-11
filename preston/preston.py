import re
from typing import Optional

import requests

from .cache import Cache


class Preston:

    BASE_URL = 'https://esi.tech.ccp.is'
    SPEC_URL = BASE_URL + '/_%s/swagger.json'
    METHODS = ['get', 'post', 'put']
    OPERATION_ID_KEY = 'operationId'
    VAR_REPLACE_REGEX = r'{(\w+)}'

    def __init__(self, version: str='latest') -> None:
        """Preston class.

        Interface for accessing the ESI.

        Args:
            version: version of the spec to load (default 'latest')

        Returns:
            None
        """
        self.cache = Cache()
        self.spec = None
        self.version = version

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
        self.spec = requests.get(self.SPEC_URL % self.version).json()
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
