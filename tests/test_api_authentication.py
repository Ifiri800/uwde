from backend.app.services.api.authentication import (
    APIAuthentication,
    APIAuthType,
)


def test_no_authentication():
    auth = APIAuthentication()

    headers, params = auth.apply(
        {"Accept": "application/json"},
        {"page": 1},
    )

    assert headers == {
        "Accept": "application/json",
    }

    assert params == {
        "page": 1,
    }


def test_api_key_header():
    auth = APIAuthentication(
        auth_type=APIAuthType.API_KEY_HEADER,
        api_key="secret-key",
        key_name="X-API-Key",
    )

    headers, params = auth.apply()

    assert headers["X-API-Key"] == "secret-key"
    assert params == {}


def test_api_key_query():
    auth = APIAuthentication(
        auth_type=APIAuthType.API_KEY_QUERY,
        api_key="secret-key",
        key_name="api_key",
    )

    headers, params = auth.apply()

    assert params["api_key"] == "secret-key"
    assert headers == {}


def test_bearer_authentication():
    auth = APIAuthentication(
        auth_type=APIAuthType.BEARER,
        token="token-value",
    )

    headers, params = auth.apply()

    assert headers["Authorization"] == "Bearer token-value"
    assert params == {}


def test_basic_authentication():
    auth = APIAuthentication(
        auth_type=APIAuthType.BASIC,
        username="user",
        password="password",
    )

    headers, params = auth.apply()

    assert headers["Authorization"].startswith(
        "Basic "
    )

    assert params == {}


def test_custom_headers():
    auth = APIAuthentication(
        auth_type=APIAuthType.CUSTOM_HEADERS,
        custom_headers={
            "X-Client-ID": "client-123",
            "X-Version": "v1",
        },
    )

    headers, params = auth.apply()

    assert headers["X-Client-ID"] == "client-123"
    assert headers["X-Version"] == "v1"
    assert params == {}


def test_auth_does_not_mutate_input():
    original_headers = {
        "Accept": "application/json",
    }

    original_params = {
        "page": 1,
    }

    auth = APIAuthentication(
        auth_type=APIAuthType.BEARER,
        token="secret",
    )

    headers, params = auth.apply(
        original_headers,
        original_params,
    )

    assert original_headers == {
        "Accept": "application/json",
    }

    assert original_params == {
        "page": 1,
    }

    assert headers is not original_headers
    assert params is not original_params


def test_safe_dict_does_not_expose_api_key():
    auth = APIAuthentication(
        auth_type=APIAuthType.API_KEY_HEADER,
        api_key="SUPER-SECRET-KEY",
    )

    data = auth.safe_dict()

    assert data["auth_type"] == "api_key_header"
    assert data["has_api_key"] is True

    assert "SUPER-SECRET-KEY" not in str(data)


def test_safe_dict_does_not_expose_token():
    auth = APIAuthentication(
        auth_type=APIAuthType.BEARER,
        token="SUPER-SECRET-TOKEN",
    )

    data = auth.safe_dict()

    assert data["has_token"] is True

    assert "SUPER-SECRET-TOKEN" not in str(data)


def test_invalid_api_key_header_requires_key():
    try:
        APIAuthentication(
            auth_type=APIAuthType.API_KEY_HEADER,
        )
    except ValueError as exc:
        assert "api_key is required" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_invalid_bearer_requires_token():
    try:
        APIAuthentication(
            auth_type=APIAuthType.BEARER,
        )
    except ValueError as exc:
        assert "token is required" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_invalid_basic_requires_credentials():
    try:
        APIAuthentication(
            auth_type=APIAuthType.BASIC,
            username="user",
        )
    except ValueError as exc:
        assert "password is required" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError"
        )
