import time
import re


__all__ = ['Cache']


class Cache:

    def __init__(self, prest, base_uri):
        """
        The cache is desgined to respect the caching rules of CREST as to
        not request a page more often than it is updated by the server.

        Args:
            prest (prest.Prest): the containing Prest instance
            base_uri (str): the root URI of CREST

        Returns:
            None
        """
        self.data = {}
        self._prest = prest
        self.logger = prest.logger
        self.fetch = prest.__call__
        self.base_uri = base_uri

    def _proper_uri(self, uri):
        """
        Covert a potentially simple string ('war') to the full URI of
        the CREST endpoint ('https://crest-tq.eveonline.com/wars/').

        Args:
            uri (str) - URI or URI fragment to modify

        Returns:
            value (str) of the proper URI
        """
        if self.base_uri not in uri:
            uri = self.base_uri + uri
        uri = re.sub(r'//', '/')
        if not uri.endswith('/'):
            uri = uri + '/'
        return uri

    def _get_expiration(self, headers):
        """
        Gets the expiration time of the data from the response headers.

        Args:
            headers (dict) - dictionary of headers from CREST

        Returns:
            value (int) of seconds from now the data expires
        """
        if headers.get('Cache-Control') in ('no-cache', 'no-store'):
            return 0
        match = re.search(r'max-age=([0-9]+)', headers.get('Cache-Control', ''))
        if match:
            return int(match.group(1))
        return 0

    def set(self, response):
        """
        Adds a response to the cache.

        Args:
            response (requests.Response) - response from CREST

        Returns:
            None
        """
        self.data[response.url] = Page(response.json(), self._get_expiration(response.headers))
        self.logger.info('Added cache for url {}, expires in {} seconds'.format(response.url, self.data[response.url].expires_in))

    def _check_expiration(self, uri, data):
        """
        Checks the expiration time for data for a URI. If the data has expired, it
        is deleted from the cache.

        Args:
            uri (str) - URI to check
            data (prest.cache.Page) - page of data for that URI

        Returns:
            value (any) of either the passed data or None if it expired
        """
        if data.expires_after < time.time():
            self.logger.warning('Cached page at uri {} expired. Now: {}, expired after: {}'.format(
                uri, time.time(), data.expires_after))
            del self.data[uri]
            data = None
        return data

    def get(self, uri, ignore_expires=False):
        """
        Get data from the cache by the URI. If the data has expired, the callback
        function is called to get the data again.

        Args:
            uri (str) - URI to get data for
            ignore_expires (bool [False]) - whether to ignore the expiration date
                in returning data to the caller

        Returns:
            value (any) of either the passed data or None if it expired
        """
        uri = self._proper_uri(uri)
        data = self.data.get(uri)
        if not data:
            return self.fetch()
        if ignore_expires:
            self._check_expiration(uri, data)
        return data.data if data else None

    def check(self, uri):
        """
        Check if data for a URI has expired. Data is not fetched again
        if it has expired.

        Args:
            uri (str) - URI to check expiration on

        Returns:
            value (bool) that's True if the data has expired
        """
        uri = self._proper_uri(uri)
        data = self.data.get(uri)
        if data:
            data = self._check_expiration(uri, data)
        return bool(data)

    def __len__(self):
        return len(self.data.keys())


class Page:

    def __init__(self, data, expires_in):
        """
        A wrapper around a page from CREST that also includes the expiration time
        in seconds and the time after which the wrapped data expires.

        Args:
            data (any) - page data from CREST
            expires_in (float) - number of seconds from now that the data expires

        Returns:
            None
        """
        self.data = data
        self.expires_in = expires_in
        self.expires_after = time.time() + expires_in
