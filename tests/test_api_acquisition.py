from backend.app.services.api.acquisition import acquire_api
from backend.app.services.api.models import APIRequest, APIResponse
from backend.app.services.api.pagination import APIPaginationConfig


def make_response(
    data,
    *,
    url="https://api.example.com/items",
    next_url=None,
):
    import json

    payload = dict(data)

    if next_url:
        payload["next"] = next_url

    return APIResponse(
        url=url,
        final_url=url,
        status_code=200,
        content_type="application/json",
        headers={},
        body=json.dumps(payload).encode("utf-8"),
    )


def test_single_page_acquisition(monkeypatch):
    responses = [
        make_response(
            {
                "items": [
                    {"id": 1, "name": "One"},
                    {"id": 2, "name": "Two"},
                ]
            }
        )
    ]

    calls = []

    def fake_execute(request, **kwargs):
        calls.append(request.url)
        return responses.pop(0)

    monkeypatch.setattr(
        "backend.app.services.api.acquisition.execute_api_request",
        fake_execute,
    )

    result = acquire_api(
        APIRequest(
            url="https://api.example.com/items"
        )
    )

    assert result.status == "success"
    assert result.record_count == 2
    assert result.pages_crawled == 1
    assert result.records[0]["id"] == 1
    assert len(calls) == 1


def test_next_url_pagination(monkeypatch):
    responses = [
        make_response(
            {
                "items": [{"id": 1}]
            },
            next_url="https://api.example.com/items?page=2",
        ),
        make_response(
            {
                "items": [{"id": 2}]
            }
        ),
    ]

    calls = []

    def fake_execute(request, **kwargs):
        calls.append(request.url)
        return responses.pop(0)

    monkeypatch.setattr(
        "backend.app.services.api.acquisition.execute_api_request",
        fake_execute,
    )

    result = acquire_api(
        APIRequest(
            url="https://api.example.com/items"
        )
    )

    assert result.status == "success"
    assert result.record_count == 2
    assert result.pages_crawled == 2
    assert calls == [
        "https://api.example.com/items",
        "https://api.example.com/items?page=2",
    ]


def test_max_pages_is_enforced(monkeypatch):
    responses = [
        make_response(
            {"items": [{"id": 1}]},
            next_url="https://api.example.com/items?page=2",
        ),
        make_response(
            {"items": [{"id": 2}]},
            next_url="https://api.example.com/items?page=3",
        ),
        make_response(
            {"items": [{"id": 3}]},
        ),
    ]

    calls = []

    def fake_execute(request, **kwargs):
        calls.append(request.url)
        return responses.pop(0)

    monkeypatch.setattr(
        "backend.app.services.api.acquisition.execute_api_request",
        fake_execute,
    )

    result = acquire_api(
        APIRequest(
            url="https://api.example.com/items"
        ),
        pagination=APIPaginationConfig(
            max_pages=2,
        ),
    )

    assert result.pages_crawled == 2
    assert result.record_count == 2
    assert len(calls) == 2


def test_max_records_is_enforced(monkeypatch):
    responses = [
        make_response(
            {
                "items": [
                    {"id": 1},
                    {"id": 2},
                    {"id": 3},
                ]
            },
            next_url="https://api.example.com/items?page=2",
        ),
    ]

    def fake_execute(request, **kwargs):
        return responses.pop(0)

    monkeypatch.setattr(
        "backend.app.services.api.acquisition.execute_api_request",
        fake_execute,
    )

    result = acquire_api(
        APIRequest(
            url="https://api.example.com/items"
        ),
        pagination=APIPaginationConfig(
            max_records=2,
        ),
    )

    assert result.record_count == 2
    assert result.records == [
        {"id": 1},
        {"id": 2},
    ]


def test_authentication_is_forwarded(monkeypatch):
    from backend.app.services.api.authentication import (
        APIAuthentication,
        APIAuthType,
    )

    captured = {}

    def fake_execute(request, **kwargs):
        captured["authentication"] = kwargs.get(
            "authentication"
        )

        return make_response(
            {
                "items": [{"id": 1}]
            }
        )

    monkeypatch.setattr(
        "backend.app.services.api.acquisition.execute_api_request",
        fake_execute,
    )

    auth = APIAuthentication(
        auth_type=APIAuthType.BEARER,
        token="secret-token",
    )

    result = acquire_api(
        APIRequest(
            url="https://api.example.com/items"
        ),
        authentication=auth,
    )

    assert result.status == "success"
    assert captured["authentication"] is auth

def test_page_pagination_strategy(monkeypatch):
    responses = [
        make_response(
            {"items": [{"id": 1}]},
            next_url=None,
        ),
        make_response(
            {"items": [{"id": 2}]},
        ),
    ]

    calls = []

    def fake_execute(request, **kwargs):
        calls.append(request.url)
        return responses.pop(0)

    monkeypatch.setattr(
        "backend.app.services.api.acquisition.execute_api_request",
        fake_execute,
    )

    # Page strategy requires a pagination signal to continue.
    # The first response provides a next URL signal.
    responses.insert(
        0,
        make_response(
            {"items": [{"id": 1}]},
            next_url="https://api.example.com/items?page=2",
        ),
    )
    responses.pop(1)

    result = acquire_api(
        APIRequest(
            url="https://api.example.com/items"
        ),
        pagination=APIPaginationConfig(
            strategy="page",
            page_size=50,
        ),
    )

    assert result.status == "success"
    assert result.record_count == 2
    assert result.pages_crawled == 2
    assert calls == [
        "https://api.example.com/items",
        "https://api.example.com/items?page=2&limit=50",
    ]


def test_offset_pagination_strategy(monkeypatch):
    responses = [
        make_response(
            {"items": [{"id": 1}]},
            next_url="https://api.example.com/items?offset=100",
        ),
        make_response(
            {"items": [{"id": 2}]},
        ),
    ]

    calls = []

    def fake_execute(request, **kwargs):
        calls.append(request.url)
        return responses.pop(0)

    monkeypatch.setattr(
        "backend.app.services.api.acquisition.execute_api_request",
        fake_execute,
    )

    result = acquire_api(
        APIRequest(
            url="https://api.example.com/items"
        ),
        pagination=APIPaginationConfig(
            strategy="offset",
            page_size=100,
        ),
    )

    assert result.status == "success"
    assert result.record_count == 2
    assert result.pages_crawled == 2


def test_cursor_pagination_strategy(monkeypatch):
    responses = [
        make_response(
            {
                "items": [{"id": 1}],
                "next_cursor": "abc123",
            }
        ),
        make_response(
            {
                "items": [{"id": 2}],
            }
        ),
    ]

    calls = []

    def fake_execute(request, **kwargs):
        calls.append(request.url)
        return responses.pop(0)

    monkeypatch.setattr(
        "backend.app.services.api.acquisition.execute_api_request",
        fake_execute,
    )

    result = acquire_api(
        APIRequest(
            url="https://api.example.com/items"
        ),
        pagination=APIPaginationConfig(
            strategy="cursor",
            page_size=25,
        ),
    )

    assert result.status == "success"
    assert result.record_count == 2
    assert result.pages_crawled == 2
    assert calls[1] == (
        "https://api.example.com/items"
        "?cursor=abc123&limit=25"
    )


def test_next_token_pagination_strategy(monkeypatch):
    responses = [
        make_response(
            {
                "items": [{"id": 1}],
                "next_token": "token123",
            }
        ),
        make_response(
            {
                "items": [{"id": 2}],
            }
        ),
    ]

    calls = []

    def fake_execute(request, **kwargs):
        calls.append(request.url)
        return responses.pop(0)

    monkeypatch.setattr(
        "backend.app.services.api.acquisition.execute_api_request",
        fake_execute,
    )

    result = acquire_api(
        APIRequest(
            url="https://api.example.com/items"
        ),
        pagination=APIPaginationConfig(
            strategy="next_token",
        ),
    )

    assert result.status == "success"
    assert result.record_count == 2
    assert result.pages_crawled == 2
    assert calls[1] == (
        "https://api.example.com/items"
        "?cursor=token123"
    )
