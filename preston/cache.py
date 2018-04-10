import time
from datetime import datetime
import re
import math


__all__ = ['Cache']


class Cache:

    def __init__(self, preston, base_url):
        """Cache class

        The cache is desgined to respect the caching rules of ESI as to
        not request a page more often than it is updated by the server.

        Args:
            preston (preston.esi.preston.Preston): the containing Preston instance
            base_url (str): the root url of ESI

        Returns:
            None
        """
        self.data = {}
        self._preston = preston
        self.base_url = base_url

    def _proper_url(self, url):
        """Converts URLs.

        Covert a potentially simple string ('alliances') to the full url of
        the ESI endpoint ('https://esi.tech.ccp.is/latest/alliances/').

        Args:
            url (str): url or url fragment to modify

        Returns:
            value (str) of the proper url
        """
        if self.base_url not in url:
            url = self.base_url + url
        url = re.sub(r'(?<!https:)//', '/', url)
        if not url.endswith('/') and '?' not in url:
            url = url + '/'
        if url.endswith('?'):
            url = url[:-1]
        return url

    def _get_expiration(self, headers):
        """Gets the expiration time of the data from the response headers.

        Args:
            headers (dict): dictionary of headers from ESI

        Returns:
            value (int) of seconds from now the data expires
        """
        expiration_str = headers.get('expires')
        if not expiration_str:
            return 0
        expiration = datetime.strptime(expiration_str, '%a, %d %b %Y %H:%M:%S %Z')
        delta = (expiration - datetime.utcnow()).total_seconds()
        return math.ceil(abs(delta))

    def set(self, response):
        """Adds a response to the cache.

        Args:
            response (requests.Response): response from ESI

        Returns:
            None
        """
        self.data[response.url] = Page(
            response.json(),
            self._get_expiration(response.headers)
        )

    def _check_expiration(self, url, data):
        """Checks the expiration time for data for a url.

        If the data has expired, it is deleted from the cache.

        Args:
            url (str): url to check
            data (preston.cache.Page): page of data for that url

        Returns:
            value (any) of either the passed data or None if it expired
        """
        if data.expires_after < time.time():
            del self.data[url]
            data = None
        return data

    def check(self, url):
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

    def __len__(self):
        """Returns the number of items in the stored data.

        More of a debugging tool, since getting the number of dictionary keys
        isn't a good indicator of how much data is actually here.

        Args:
            None

        Returns:
            value (int) of the number of keys in the data
        """
        return len(self.data.keys())


class Page:

    def __init__(self, data, expires_in):
        """Page class

        A wrapper around a page from ESI that also includes the expiration time
        in seconds and the time after which the wrapped data expires.

        Args:
            data (any): page data from ESI
            expires_in (float): number of seconds from now that the data expires

        Returns:
            None
        """
        self.data = data
        self.expires_in = expires_in
        self.expires_after = time.time() + expires_in
