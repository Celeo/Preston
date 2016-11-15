from time import sleep
from datetime import datetime, timedelta

import pytest

from preston.esi.preston import Preston, base_url


@pytest.fixture(scope='module')
def preston():
    """ Test fixture to provide a `preston.esi.preston.Preston` object to all methods. """
    return Preston()


def test_initialization_size(preston):
    """ Test the initial size of the cache. """
    assert len(preston.cache.data) == 0


def test_proper_url(preston):
    """ Test the url formatting method. """
    assert preston.cache._proper_url('') == base_url
    assert preston.cache._proper_url('wars') == base_url + 'wars/'
    assert preston.cache._proper_url(base_url + 'wars') == base_url + 'wars/'


def test_expiration(preston):
    """ Test the expiration calculation method. """
    assert preston.cache._get_expiration({}) == 0
    assert(preston.cache._get_expiration({
        'expires': (datetime.utcnow() + timedelta(seconds=1)).strftime('%a, %d %b %Y %H:%M:%S GMT')
    }) == 1)
    assert(preston.cache._get_expiration({
        'expires': (datetime.utcnow() + timedelta(seconds=100)).strftime('%a, %d %b %Y %H:%M:%S GMT')
    }) == 100)
    assert(preston.cache._get_expiration({
        'expires': (datetime.utcnow() + timedelta(seconds=1234576890)).strftime('%a, %d %b %Y %H:%M:%S GMT')
    }) == 1234576890)


def test_add_verify_page(preston):
    """ Test adding and validating data to the cache. """
    class Response:

        def __init__(self, url, data=None, headers=None):
            """
            Emulate a `requests.Response` object.
            """
            self.url = preston.cache._proper_url(url)
            self.data = data or {}
            self.headers = {
                'expires': (datetime.utcnow() + timedelta(seconds=300)).strftime('%a, %d %b %Y %H:%M:%S GMT')
            }
            if headers:
                self.headers.update(headers)

        def json(self):
            return self.data

    preston.cache.data.clear()
    r = Response('')
    preston.cache.set(r)
    assert len(preston.cache) == 1
    assert preston.cache.check('') == {}

    r = Response(base_url + 'test', {'foo': 'bar'})
    preston.cache.set(r)
    assert len(preston.cache) == 2
    assert preston.cache.check('test') == {'foo': 'bar'}

    r = Response(base_url + 'test2', {}, {
        'expires': (datetime.utcnow() + timedelta(seconds=1)).strftime('%a, %d %b %Y %H:%M:%S GMT')
    })
    preston.cache.set(r)
    assert len(preston.cache) == 3
    sleep(1)
    assert not preston.cache.check('test2')
    assert len(preston.cache) == 2
