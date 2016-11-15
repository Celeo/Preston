import pytest

from preston.xmlapi import *


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


def test_eve_charid(preston):
    """
    Test the character name to id match for 'Celeo Servasse'
    """
    data = preston.eve.CharacterId(names='Celeo Servasse')
    assert data['rowset']['row']['@characterID'] == '91316135'
