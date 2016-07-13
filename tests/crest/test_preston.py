import pytest

from preston.crest import *


@pytest.fixture(scope='module')
def preston():
    """
    Test fixture to provide a `preston.Preston` object to all methods.
    """
    return Preston()


def test_initialization(preston):
    """
    Test that the object initialized without error.
    """
    pass


def test_single_page_element(preston):
    """
    Test getting an element from the base CREST page.
    """
    assert(preston.serverName)


def test_second_page(preston):
    """
    Test getting a page off of the base CREST page.
    """
    assert(preston.incursions())


def test_second_page_element(preston):
    """
    Test gettign an element from a page off of the base CREST page.
    """
    assert(preston.incursions().totalCount)


def test_single_page_sub_link(preston):
    """
    Test accessing a page from a base CREST page subitem.
    """
    assert(preston.sovereignty.campaigns())


def test_find_method(preston):
    """
    Test using the find method.
    """
    assert(preston.systems().items.find(name='Jita')().planets[3].moons[3]().name)


def test_getitem(preston):
    """
    Test getting an item by an index instead of attribute.
    """
    assert(preston.bloodlines().items[0].race())
