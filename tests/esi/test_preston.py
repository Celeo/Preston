import pytest

from preston.esi import *


@pytest.fixture(scope='module')
def preston():
    """ Test fixture to provide a `preston.Preston` object to all methods. """
    return Preston()


def test_initialization(preston):
    """ Test that the object initialized without error. """
    pass


def test_versioning(preston):
    """ Test versioning """
    assert preston.version == 'latest'
    assert preston.v1.version == 'v1'
    assert preston.v100.version == 'v100'
    assert preston.latest.version == 'latest'
    assert preston.dev.version == 'dev'
    assert preston.legacy.version == 'legacy'


def test_alliance_list(preston):
    """ Test endpoints """
    result = preston.alliances()
    assert result
    assert type(result) == list


def test_get_alliance_name(preston):
    """ Test endpoints """
    result = preston.alliances.names(alliance_ids=99006650)
    assert result == [{
        'alliance_id': 99006650,
        'alliance_name': 'The Society For Unethical Treatment Of Sleepers'
    }]


def test_get_alliance_members(preston):
    """ Test endpoints """
    result = preston.alliances['99006650'].corporations()
    assert type(result) == list


def test_get_char_public_info(preston):
    """ Check public character information """
    result = preston.characters(91316135)
    assert type(result) == dict
    assert result['ancestry_id'] == 15
    assert result['birthday'] == '2011-10-18T16:57:00Z'
    assert result['race_id'] == 8
    assert result['gender'] == 'male'
    assert result['bloodline_id'] == 7
    assert result['name'] == 'Celeo Servasse'
    assert type(result['description']) == str
    assert type(result['corporation_id']) == int
    assert type(result['security_status']) == float
