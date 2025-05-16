from time import sleep
from datetime import datetime, timedelta, UTC

import pytest

from preston.preston import Preston
from preston.cache import Cache


@pytest.fixture
def cache():
    return Cache()


def test_initialization_size(cache):
    assert len(cache.data) == 0


def test_expiration(cache):
    assert cache._get_expiration({}) == 0
    assert (
        cache._get_expiration(
            {
                "expires": (datetime.now(UTC) + timedelta(seconds=1)).strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                )
            }
        )
        == 1
    )
    assert (
        cache._get_expiration(
            {
                "expires": (datetime.now(UTC) + timedelta(seconds=100)).strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                )
            }
        )
        == 100
    )
    assert (
        cache._get_expiration(
            {
                "expires": (datetime.now(UTC) + timedelta(seconds=1234576890)).strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                )
            }
        )
        == 1234576890
    )


def test_add_verify_page(cache):
    class Response:
        def __init__(self, url, data=None, headers=None):
            self.url = url
            self.data = data or {}
            self.headers = {
                "expires": (datetime.now(UTC) + timedelta(seconds=300)).strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                )
            }
            if headers:
                self.headers.update(headers)

        def json(self):
            return self.data

    cache.data.clear()
    r = Response("")
    cache.set(r.data, r.headers, r.url)
    assert len(cache) == 1
    assert cache.check("") == {}

    r = Response(Preston.BASE_URL + "/test", {"foo": "bar"})
    cache.set(r.data, r.headers, r.url)
    assert len(cache) == 2
    assert cache.check(Preston.BASE_URL + "/test") == {"foo": "bar"}

    r = Response(
        Preston.BASE_URL + "/test2",
        {},
        {
            "expires": (datetime.now(UTC) + timedelta(seconds=1)).strftime(
                "%a, %d %b %Y %H:%M:%S GMT"
            )
        },
    )
    cache.set(r.data, r.headers, r.url)
    assert len(cache) == 3
    sleep(1)
    assert not cache.check(Preston.BASE_URL + "/test2")
    assert len(cache) == 2
