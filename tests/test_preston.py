import time
from datetime import UTC, datetime

import pytest

from preston import Preston


OPENAPI_SPEC = {
    "openapi": "3.1.0",
    "paths": {
        "/characters/{character_id}": {
            "parameters": [{"name": "character_id", "in": "path"}],
            "get": {"operationId": "GetCharactersCharacterId"},
        },
        "/characters/affiliation": {
            "post": {"operationId": "PostCharactersAffiliation"},
        },
        "/characters/{character_id}/contacts": {
            "delete": {"operationId": "DeleteCharactersCharacterIdContacts"},
        },
        "/characters/{character_id}/calendar/{event_id}": {
            "put": {"operationId": "PutCharactersCharacterIdCalendarEventId"},
        },
    },
}


@pytest.fixture
def empty():
    return Preston(compatibility_date="2026-08-04")


@pytest.fixture
def sample():
    return Preston(
        compatibility_date="2026-08-04",
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
    assert empty.compatibility_date == "2026-08-04"
    assert empty.session.headers["X-Compatibility-Date"] == "2026-08-04"


def test_kwargs_setters(sample):
    assert sample.cache is not None
    assert sample.spec is None
    assert sample.version == "latest"
    assert sample.compatibility_date == "2026-08-04"
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
    assert new.compatibility_date == sample.compatibility_date
    assert new.session.headers["X-Compatibility-Date"] == sample.compatibility_date


def test_legacy_version_is_deprecated_but_retained():
    with pytest.warns(DeprecationWarning, match="compatibility_date"):
        preston = Preston(version="5", compatibility_date="2026-08-04")
    assert preston.version == "5"
    assert preston.compatibility_date == "2026-08-04"


def test_current_compatibility_date_changes_at_downtime():
    assert Preston._current_compatibility_date(
        datetime(2026, 8, 13, 10, 59, tzinfo=UTC)
    ) == "2026-08-12"
    assert Preston._current_compatibility_date(
        datetime(2026, 8, 13, 11, 0, tzinfo=UTC)
    ) == "2026-08-13"


def test_invalid_compatibility_date_is_rejected():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        Preston(compatibility_date="August 4, 2026")


def test_get_authorization_headers(empty):
    expected = "Basic c29tZV9jbGllbnRfaWQ6c29tZV9jbGllbnRfc2VjcmV0"
    empty.client_id = "some_client_id"
    empty.client_secret = "some_client_secret"
    assert expected == empty._get_authorization_headers()["Authorization"]


def test_get_spec_uses_openapi_session_and_excludes_authorization(empty, monkeypatch):
    calls = []

    def get_spec(request_function, target_url, **kwargs):
        calls.append((request_function, target_url, kwargs))
        return OPENAPI_SPEC

    monkeypatch.setattr(empty, "_retry_request", get_spec)

    assert empty._get_spec() == OPENAPI_SPEC
    assert calls == [
        (
            empty.session.get,
            "https://esi.evetech.net/meta/openapi.json",
            {"headers": {"Authorization": None}},
        )
    ]
    assert "swagger.json" not in Preston.SPEC_URL


@pytest.mark.parametrize(
    ("operation_id", "expected_path"),
    [
        ("GetCharactersCharacterId", "/characters/{character_id}"),
        ("get_characters_character_id", "/characters/{character_id}"),
        ("PostCharactersAffiliation", "/characters/affiliation"),
        ("post_characters_affiliation", "/characters/affiliation"),
        (
            "DeleteCharactersCharacterIdContacts",
            "/characters/{character_id}/contacts",
        ),
        (
            "delete_characters_character_id_contacts",
            "/characters/{character_id}/contacts",
        ),
        (
            "put_characters_character_id_calendar_event_id",
            "/characters/{character_id}/calendar/{event_id}",
        ),
    ],
)
def test_get_path_for_openapi_and_legacy_operation_ids(
    empty, operation_id, expected_path
):
    empty.spec = OPENAPI_SPEC
    assert empty._get_path_for_op_id(operation_id) == expected_path


def test_legacy_operation_id_splits_acronyms_and_numbers():
    assert Preston._legacy_operation_id("GetESIStatusV2") == "get_esi_status_v2"


def test_legacy_path_operation_id_handles_semantic_openapi_ids(empty):
    empty.spec = {
        "openapi": "3.1.0",
        "paths": {
            "/characters/{character_id}": {
                "get": {"operationId": "GetCharactersDetail"},
            }
        },
    }
    assert empty._get_path_for_op_id("GetCharactersDetail") == "/characters/{character_id}"
    assert (
        empty._get_path_for_op_id("get_characters_character_id")
        == "/characters/{character_id}"
    )


def test_unknown_operation_id_has_a_useful_error(empty):
    empty.spec = OPENAPI_SPEC
    with pytest.raises(ValueError, match="Unknown ESI operation ID 'not_an_operation'"):
        empty._get_path_for_op_id("not_an_operation")


def test_openapi_ignores_non_http_path_item_keys(empty):
    empty.spec = {
        "openapi": "3.1.0",
        "paths": {
            "/status": {
                "parameters": [],
                "$ref": "#/components/pathItems/status",
                "trace": {"operationId": "TraceStatus"},
                "get": {"operationId": "GetStatus"},
            }
        },
    }
    assert empty._get_path_for_op_id("get_status") == "/status"
    with pytest.raises(ValueError, match="TraceStatus"):
        empty._get_path_for_op_id("TraceStatus")


def test_openapi_duplicate_legacy_ids_raise_an_error(empty):
    empty.spec = {
        "openapi": "3.1.0",
        "paths": {
            "/one": {"get": {"operationId": "GetURLValue"}},
            "/two": {"get": {"operationId": "GetUrlValue"}},
        },
    }
    with pytest.raises(ValueError, match="ambiguous legacy alias 'get_url_value'"):
        empty._get_path_for_op_id("GetURLValue")


def test_malformed_openapi_paths_raise_an_error(empty, monkeypatch):
    monkeypatch.setattr(empty, "_retry_request", lambda *args, **kwargs: {"openapi": "3.1.0"})
    with pytest.raises(ValueError, match="missing a paths object"):
        empty._get_spec()


def test_openapi_operation_without_an_id_raises_an_error(empty):
    empty.spec = {"openapi": "3.1.0", "paths": {"/status": {"get": {}}}}
    with pytest.raises(ValueError, match="GET /status is missing an operationId"):
        empty._get_path_for_op_id("get_status")


def test_operation_helpers_use_openapi_paths(empty, monkeypatch):
    empty.spec = OPENAPI_SPEC
    monkeypatch.setattr(empty, "get_path", lambda path, data: (path, data))
    monkeypatch.setattr(
        empty, "post_path", lambda path, path_data, post_data: (path, path_data, post_data)
    )
    monkeypatch.setattr(empty, "delete_path", lambda path, path_data: (path, path_data))

    assert empty.get_op("get_characters_character_id", character_id=91316135) == (
        "/characters/{character_id}",
        {"character_id": 91316135},
    )
    assert empty.post_op("PostCharactersAffiliation", {"page": 1}, {"ids": [1]}) == (
        "/characters/affiliation",
        {"page": 1},
        {"ids": [1]},
    )
    assert empty.delete_op(
        "delete_characters_character_id_contacts", {"character_id": 91316135}
    ) == ("/characters/{character_id}/contacts", {"character_id": 91316135})


def test_get_path_uses_session_with_compatibility_date(empty, monkeypatch):
    calls = []

    def get_response(request_function, target_url, **kwargs):
        calls.append((request_function, target_url, kwargs))
        return {"ok": True}, {}, target_url

    monkeypatch.setattr(empty, "_retry_request", get_response)

    assert empty.get_path("/status", {}) == {"ok": True}
    assert calls == [(empty.session.get, "https://esi.evetech.net/status", {"return_metadata": True})]
    assert empty.session.headers["X-Compatibility-Date"] == "2026-08-04"


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


def test_authenticated_preston_retains_compatibility_date(empty, monkeypatch):
    monkeypatch.setattr(
        empty,
        "_retry_request",
        lambda *args, **kwargs: {
            "access_token": "token",
            "expires_in": 60,
            "refresh_token": "refresh",
        },
    )
    authenticated = empty.authenticate("authorization-code")
    assert authenticated.compatibility_date == empty.compatibility_date
    assert (
        authenticated.session.headers["X-Compatibility-Date"]
        == empty.compatibility_date
    )
