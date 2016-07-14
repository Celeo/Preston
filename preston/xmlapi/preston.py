from urllib.parse import urlencode

import requests
import xmltodict

from preston.xmlapi.cache import Cache


__all__ = ['Preston']


class Preston:

    def __init__(self, key=None, code=None, user_agent='', cache=None):
        """
        This class is the base for access the XML API. Attributes
        can be called on it to build a path to an endpoint.

        Args:
            key (str) - optional authentication keyID
            code (str) - optional authentication vCode
            user_agent (str) - optional (recommended) User-Agent
                                to use when making web requests
            cache (preston.xmlapi.cache.Cache) - page cache

        Returns:
            None
        """
        self.cache = cache or Cache()
        self.user_agent = user_agent or 'Preston (github.com/Celeo/Preston)'
        self.session = requests.session()
        self.session.headers.update({'User-Agent': self.user_agent})
        self.key = key
        self.code = code

    def __getattr__(self, key):
        """
        Build a path towards an endpoint.

        Args:
            key (str) - path to append

        Returns:
            new class (preston.xmlapi.preston.Path) to that endpoint
        """
        return Path(self, key, self.cache, self.key, self.code)


class Path:

    def __init__(self, preston, path, cache, key, code):
        """
        This is the class that is built up and called when
        getting an XML API endpoint.

        Args:
            preston (preston.xmlapi.preston.Preston) - Preston instance
            path (str) - path to the endpoint
            cache (preston.xmlapi.cache.Cache) - page storage cache
            key (str) - API keyID
            code (str) - API vCode

        Returns:
            None
        """
        self.preston = preston
        self.path = path
        self.cache = cache
        self.key = key
        self.code = code

    def __getattr__(self, key):
        """
        Build a path towards an endpoint.

        Args:
            key (str) - path to append

        Returns:
            new class (preston.xmlapi.preston.Path) to that endpoint
        """
        return Path(self.preston, self.path + '/' + key, self.cache, self.key, self.code)

    def __call__(self, *args, **kwargs):
        """
        Get data for the endpoint. If the page already exists in the cache
        and hasn't yet expired, it is returned from the cache and no
        web request is made. If the data is expired or not in the cache at
        all, then a new web request is made, the data formatted, stored in
        the cache, and then returned to the caller.

        Args:
            *args (tuple) - not currently used
            **kwargs (dict) - optional parameters to encode and send to
                                the web endpoint

        Returns:
            value (dict) of the page's XML converted to a dictionary
        """
        url = 'https://api.eveonline.com/' + self.path + '.xml.aspx'
        url += '?' + urlencode(kwargs)
        if self.key and self.code:
            url += '&' + urlencode({'keyID': self.key, 'vCode': self.code})
        print
        cached = self.cache.get(url)
        if cached:
            return cached
        data = xmltodict.parse(requests.get(url).text)['eveapi']
        self.cache.set(url, data['result'], data['cachedUntil'])
        return data['result']
