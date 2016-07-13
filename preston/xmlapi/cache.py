from datetime import datetime


__all__ = ['Cache']


class Cache:

    def __init__(self):
        """
        The cache is designed to respect the caching rules of the XML API
        as to not request a page more often than it is updated by the server.

        Args:
            None

        Returns:
            None
        """
        self.data = {}

    def set(self, url, data, expiration):
        """
        Store a page into the internal dictionary.

        Args:
            url (str) - the URL the page was retrieved from
            data (str) - the page's contents
            expiration (str) - the page's expiration datetime

        Returns:
            None
        """
        self.data[url] = Page(data, expiration)

    def get(self, url):
        """
        Checks the internal dictionary for the page and returns
        it if it's found.

        This method checks the expiration datetime of the page
        before returning it. If it's expired, None is returned.

        Args:
            url (str) - URL to check

        Returns:
            value (dict) of the page contents or None
        """
        page = self.data.get(url)
        if not page:
            return None
        if datetime.utcnow() > page.expires_after:
            del self.data[url]
            return None
        return page.data


class Page:

    def __init__(self, data, expires_after):
        """
        A wrapper around a page from the XML API that also includes
        the datetime after which the page's data is expired.

        Args:
            data (any) - page data from CREST
            expires_after (datetime) - datetime for data expiration

        Returns:
            None
        """
        self.data = data
        self.expires_after = datetime.strptime(expires_after, '%Y-%m-%d %H:%M:%S')
