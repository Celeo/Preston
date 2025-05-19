import time

import pytest

from preston import Preston


@pytest.fixture
def empty():
    return Preston()


@pytest.fixture
def sample():
    return Preston(
        version="1",
        client_id="2",
        client_secret="3",
        callback_url="4",
        scope="5",
        access_token="6",
        access_expiration="7",
        refresh_token="8",
        no_update_token=True,
    )


def test_starting_point(empty):
    assert empty.cache is not None
    assert empty.spec is None
    assert empty.version is not None


def test_kwargs_setters(sample):
    assert sample.cache is not None
    assert sample.spec is None
    assert sample.version == "1"
    assert sample.client_id == "2"
    assert sample.client_secret == "3"
    assert sample.callback_url == "4"
    assert sample.scope == "5"
    assert sample.access_token == "6"
    assert sample.access_expiration == "7"
    assert sample.refresh_token == "8"


def test_copy(sample):
    new = sample.copy()
    new.access_token = None
    assert sample.access_token is not None


def test_get_authorization_headers(empty):
    expected = "Basic c29tZV9jbGllbnRfaWQ6c29tZV9jbGllbnRfc2VjcmV0"
    empty.client_id = "some_client_id"
    empty.client_secret = "some_client_secret"
    assert expected == empty._get_authorization_headers()["Authorization"]


def test_get_path_for_op_id(empty):
    empty.spec = {
        "paths": {
            "a": {"get": {"operationId": "a-id"}},
            "b": {"put": {"operationId": "b-id"}},
            "c": {"delete": {"operationId": "c-id"}},
        }
    }
    assert empty._get_path_for_op_id("a-id") == "a"
    assert empty._get_path_for_op_id("b-id") == "b"
    assert empty._get_path_for_op_id("c-id") == "c"
    assert empty._get_path_for_op_id("d-id") is None


def test_is_access_token_expired(empty):
    empty.access_expiration = 0
    assert empty._is_access_token_expired()
    empty.access_expiration = time.time() + 1000
    assert not empty._is_access_token_expired()


def test_get_authorize_url(sample):
    expected = "https://login.eveonline.com/v2/oauth/authorize?response_type=code&redirect_uri=4&client_id=2&scope=5&state=some_state"
    assert sample.get_authorize_url("some_state") == expected
    sample_multiple_scopes = sample
    sample_multiple_scopes.scope = "scope scope1"
    expected_multiple_scope = "https://login.eveonline.com/v2/oauth/authorize?response_type=code&redirect_uri=4&client_id=2&scope=scope%20scope1&state=other_state"
    assert (
        sample_multiple_scopes.get_authorize_url("other_state")
        == expected_multiple_scope
    )


def test_insert_vars(empty):
    data = dict(foo="bar", bar="baz")
    test_cases = [
        ["/foo/bar", "/foo/bar", data],
        ["/foo/{bar}", "/foo/baz", {"foo": "bar"}],
        ["/{foo}/bar", "/bar/bar", {"bar": "baz"}],
        ["/{foo}/{bar}", "/bar/baz", {}],
    ]
    for case in test_cases:
        res = empty._insert_vars(case[0], data)
        assert res[0] == case[1]
        assert res[1] == case[2]


def test_insert_vars_missing(empty):
    res = empty._insert_vars("/foo/{bar}", {})
    assert res[0] == "/foo/"
    assert res[1] == {}


def test_whoami_unauthorized(empty):
    assert empty.whoami() == {}


def test_try_refresh_access_token_empty(empty):
    empty._try_refresh_access_token()
    assert empty.refresh_token is None
    assert empty.access_token is None


def test_try_refresh_access_token_has(empty):
    empty.refresh_token = "abc123"
    empty.access_token = None
    empty._is_access_token_expired = lambda: False
    empty.access_expiration = 1.0
    empty.refresh_token_callback = lambda *args: None
    empty._retry_request = lambda *args, **kwargs: {
        "access_token": "def",
        "expires_in": 1,
        "refresh_token": "qwe",
    }
    empty._try_refresh_access_token()
    assert empty.access_token == "def"
