import pytest

from preston.preston import Preston


@pytest.fixture
def preston():
    return Preston()


def test_starting_point(preston):
    assert preston.spec is None
    assert preston.cache is not None
    assert preston.version is not None


def test_get_spec_cache(preston):
    preston.spec = {}
    assert preston.spec == {}
