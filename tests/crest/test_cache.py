from time import sleep

import pytest

from preston.crest.preston import Preston, base_url


@pytest.fixture(scope='module')
def preston():
    """
    Test fixture to provide a `preston.crest.preston.Preston` object to all methods.
    """
    return Preston()


def test_initialization_size(preston):
    """
    Test the initial size of the cache, which should be 1 since
    `preston.Preston` fetches the base url data on initialization.
    """
    assert len(preston.cache.data) == 1


def test_proper_url(preston):
    """
    Test the url formatting method.
    """
    assert preston.cache._proper_url('') == base_url
    assert preston.cache._proper_url('wars') == base_url + 'wars/'
    assert preston.cache._proper_url(base_url + 'wars') == base_url + 'wars/'


def test_expiration(preston):
    """
    Test the expiration calculation method.
    """
    assert preston.cache._get_expiration({}) == 0
    assert preston.cache._get_expiration({'Cache-Control': 'no-cache'}) == 0
    assert preston.cache._get_expiration({'Cache-Control': 'no-store'}) == 0
    assert preston.cache._get_expiration({'Cache-Control': 'max-age=1'}) == 1
    assert preston.cache._get_expiration({'Cache-Control': 'max-age=100'}) == 100
    assert preston.cache._get_expiration({'Cache-Control': 'max-age=1234576890'}) == 1234576890


def test_add_verify_page(preston):
    """
    Test adding and validating data to the cache.
    """
    class Response:

        def __init__(self, url, data=None, headers=None):
            """
            Emulate a `requests.Response` object.
            """
            self.url = preston.cache._proper_url(url)
            self.data = data or {}
            self.headers = {'Cache-Control': 'max-age=300'}
            if headers:
                self.headers.update(headers)

        def json(self):
            return self.data

    preston.cache.data.clear()
    r = Response('')
    preston.cache.set(r)
    assert len(preston.cache) == 1
    assert preston.cache.check('')
    assert preston.cache.get('') == {}

    r = Response(base_url + 'test', {'foo': 'bar'})
    preston.cache.set(r)
    assert len(preston.cache) == 2
    assert preston.cache.check('test')
    assert preston.cache.get('test') == {'foo': 'bar'}

    r = Response(base_url + 'test2', {}, {'Cache-Control': 'max-age=1'})
    preston.cache.set(r)
    assert len(preston.cache) == 3
    sleep(1)
    assert not preston.cache.check('test2')
    assert len(preston.cache) == 2
