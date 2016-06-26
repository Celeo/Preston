from time import sleep

import pytest

from prest.prest import Prest, base_uri


@pytest.fixture(scope='module')
def prest():
    """
    Test fixture to provide a `prest.Prest` object to all methods.
    """
    return Prest()


def test_initialization_size(prest):
    """
    Test the initial size of the cache, which should be 1 since
    `prest.Prest` fetches the base URI data on initialization.
    """
    assert(len(prest.cache.data) == 1)


def test_proper_uri(prest):
    """
    Test the URI formatting method.
    """
    assert(prest.cache._proper_uri('') == base_uri)
    assert(prest.cache._proper_uri('wars') == base_uri + 'wars')
    assert(prest.cache._proper_uri(base_uri + 'wars') == base_uri + 'wars')


def test_expiration(prest):
    """
    Test the expiration calculation method.
    """
    assert(prest.cache._get_expiration({}) == 0)
    assert(prest.cache._get_expiration({'Cache-Control': 'no-cache'}) == 0)
    assert(prest.cache._get_expiration({'Cache-Control': 'no-store'}) == 0)
    assert(prest.cache._get_expiration({'Cache-Control': 'max-age=1'}) == 1)
    assert(prest.cache._get_expiration({'Cache-Control': 'max-age=100'}) == 100)
    assert(prest.cache._get_expiration({'Cache-Control': 'max-age=1234576890'}) == 1234576890)


def test_add_verify_page(prest):
    """
    Test adding and validating data to the cache.
    """
    class Response:

        def __init__(self, url, data=None, headers=None):
            """
            Emulate a `requests.Response` object.
            """
            self.url = prest.cache._proper_uri(url)
            self.data = data or {}
            self.headers = {'Cache-Control': 'max-age=300'}
            if headers:
                self.headers.update(headers)

        def json(self):
            return self.data

    prest.cache.data.clear()
    r = Response('')
    prest.cache.set(r)
    assert(len(prest.cache) == 1)
    assert(prest.cache.check(''))
    assert(prest.cache.get('') == {})

    r = Response(base_uri + 'test', {'foo': 'bar'})
    prest.cache.set(r)
    assert(len(prest.cache) == 2)
    assert(prest.cache.check('test'))
    assert(prest.cache.get('test') == {'foo': 'bar'})

    r = Response(base_uri + 'test2', {}, {'Cache-Control': 'max-age=1'})
    prest.cache.set(r)
    assert(len(prest.cache) == 3)
    sleep(1)
    assert(not prest.cache.check('test2'))
    assert(len(prest.cache) == 2)
