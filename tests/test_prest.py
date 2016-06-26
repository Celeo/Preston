import pytest

from prest import *


@pytest.fixture(scope='module')
def prest():
    """
    Test fixture to provide a `prest.Prest` object to all methods.
    """
    return Prest()


def test_initialization(prest):
    """
    Test that the object initialized without error.
    """
    pass


def test_single_page_element(prest):
    """
    Test getting an element from the base CREST page.
    """
    assert(prest.serverName)


def test_second_page(prest):
    """
    Test getting a page off of the base CREST page.
    """
    assert(prest.incursions())


def test_second_page_element(prest):
    """
    Test gettign an element from a page off of the base CREST page.
    """
    assert(prest.incursions().totalCount)


def test_single_page_sub_link(prest):
    """
    Test accessing a page from a base CREST page subitem.
    """
    assert(prest.sovereignty.campaigns())


def test_find_method(prest):
    """
    Test using the find method.
    """
    assert(prest.systems().items.find(name='Jita')().planets[3].moons[3]().name)


def test_getitem(prest):
    """
    Test getting an item by an index instead of attribute.
    """
    assert(prest.bloodlines().items[0].race())
