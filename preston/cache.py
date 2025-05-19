from datetime import datetime, UTC
import math
import time
from typing import Optional


class Cache:
    def __init__(self):
        """Cache class.

        The cache is designed to respect the caching rules of ESI as to
        not request a page more often than it is updated by the server.

        Args:
            None

        Returns:
            None
        """
        self.data: dict = {}

    def _get_expiration(self, headers: dict) -> int:
        """Gets the expiration time of the data from the response headers.

        Args:
            headers: dictionary of headers from ESI

        Returns:
            value of seconds from now the data expires
        """
        expiration_str = headers.get("expires")
        if not expiration_str:
            return 0
        expiration = datetime.strptime(expiration_str, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=UTC)
        delta = (expiration - datetime.now(UTC)).total_seconds()
        return math.ceil(abs(delta))

    def set(self, data: dict, headers: dict, url: str) -> None:
        """Adds a response to the cache.

        Args:
            data: response from ESI
            headers: headers from ESI
            url: url for the request

        Returns:
            None
        """
        self.data[url] = SavedEndpoint(
            data, self._get_expiration(headers)
        )

    def _check_expiration(self, url: str, data: "SavedEndpoint") -> "SavedEndpoint":
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

    def check(self, url: str) -> Optional[dict]:
        """Check if data for a url has expired.

        Data is not fetched again if it has expired.

        Args:
            url: url to check expiration on

        Returns:
            value of the data, possibly None
        """
        data = self.data.get(url)
        if data:
            data = self._check_expiration(url, data)
        return data.data if data else None

    def __len__(self) -> int:
        """Returns the number of items in the stored data.

        More of a debugging tool, since getting the number of dictionary keys
        isn't a good indicator of how much data is actually here.

        Args:
            None

        Returns:
            value of the number of keys in the data
        """
        return len(self.data.keys())


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
