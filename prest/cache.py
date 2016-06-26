import time
import re


__all__ = ['Cache']


class Cache:

    def __init__(self, prest, base_uri):
        self.data = {}
        self._prest = prest
        self.logger = prest.logger
        self.fetch = prest.__call__
        self.base_uri = base_uri

    def _proper_uri(self, uri):
        if self.base_uri not in uri:
            uri = self.base_uri + uri
        return uri

    def _get_expiration(self, headers):
        if headers.get('Cache-Control') in ('no-cache', 'no-store'):
            return 0
        match = re.search(r'max-age=([0-9]+)', headers.get('Cache-Control'))
        if match:
            return int(match.group(1))
        return 0

    def set(self, response):
        self.data[response.url] = Page(response.json(), self._get_expiration(response.headers))
        self.logger.info('Added cache for url {}, expires in {} seconds'.format(response.url, self.data[response.url].expires_in))

    def _check_expiration(self, uri, data):
        if data.expires_after < time.time():
            self.logger.warning('Cached page at uri {} expired. Now: {}, expired after: {}'.format(
                uri, time.time(), data.expires_after))
            del self.data[uri]
            data = None
        else:
            self.logger.info('Returning cached page at uri {}'.format(uri))
        return data

    def get(self, uri, ignore_expires=False):
        uri = self._proper_uri(uri)
        data = self.data.get(uri)
        if not data:
            return self.fetch()
        if ignore_expires:
            self._check_expiration(uri, data)
        return data.data if data else None

    def check(self, uri):
        uri = self._proper_uri(uri)
        data = self.data.get(uri)
        if data:
            if data.expires_after < time.time():
                self.logger.warning('Cached page at uri {} expired. Now: {}, expired after: {}'.format(
                    uri, time.time(), data.expires_after))
                del self.data[uri]
                data = None
        return bool(data)

    def __len__(self):
        return len(self.data.keys())


class Page:

    def __init__(self, data, expires_in):
        self.data = data
        self.expires_in = expires_in
        self.expires_after = time.time() + expires_in
