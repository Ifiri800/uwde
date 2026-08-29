import pytest

from backend.app.services.api.pagination import (
    APIPaginationConfig,
    APIPaginationState,
    build_cursor_url,
    build_next_token_url,
    build_offset_url,
    build_page_url,
    detect_api_pagination,
)


def test_detects_next_url():
    result = detect_api_pagination(
        {
            "next": "https://example.com/api?page=2"
        },
        current_url="https://example.com/api?page=1",
    )

    assert result.has_next is True
    assert result.next_url == (
        "https://example.com/api?page=2"
    )


def test_detects_nested_next_url():
    result = detect_api_pagination(
        {
            "pagination": {
                "next_url": "/api?page=2"
            }
        },
        current_url="https://example.com/api?page=1",
    )

    assert result.next_url == "/api?page=2"


def test_detects_cursor():
    result = detect_api_pagination(
        {
            "next_cursor": "abc123"
        },
        current_url="https://example.com/api",
    )

    assert result.cursor == "abc123"


def test_detects_next_token():
    result = detect_api_pagination(
        {
            "next_token": "token123"
        },
        current_url="https://example.com/api",
    )

    assert result.next_token == "token123"


def test_detects_link_header():
    result = detect_api_pagination(
        {},
        current_url="https://example.com/api?page=1",
        headers={
            "Link": (
                '<https://example.com/api?page=2>; '
                'rel="next"'
            )
        },
    )

    assert result.next_url == (
        "https://example.com/api?page=2"
    )


def test_build_page_url():
    result = build_page_url(
        "https://example.com/api?category=jobs",
        APIPaginationConfig(
            strategy="page",
            page_size=50,
        ),
        2,
    )

    assert "category=jobs" in result
    assert "page=2" in result
    assert "limit=50" in result


def test_build_offset_url():
    result = build_offset_url(
        "https://example.com/api",
        APIPaginationConfig(
            strategy="offset",
            page_size=25,
        ),
        25,
    )

    assert "offset=25" in result
    assert "limit=25" in result


def test_build_cursor_url():
    result = build_cursor_url(
        "https://example.com/api",
        APIPaginationConfig(
            strategy="cursor",
        ),
        "abc123",
    )

    assert "cursor=abc123" in result
    assert "limit=100" in result


def test_build_next_token_url():
    result = build_next_token_url(
        "https://example.com/api",
        token="token123",
    )

    assert "next_token=token123" in result


def test_pagination_state_stops_at_max_pages():
    config = APIPaginationConfig(
        strategy="page",
        max_pages=2,
    )

    state = APIPaginationState(
        pages_crawled=2,
        records_collected=10,
    )

    assert state.can_continue(config) is False


def test_pagination_state_stops_at_max_records():
    config = APIPaginationConfig(
        strategy="page",
        max_records=10,
    )

    state = APIPaginationState(
        pages_crawled=1,
        records_collected=10,
    )

    assert state.can_continue(config) is False


def test_invalid_pagination_strategy():
    with pytest.raises(ValueError):
        APIPaginationConfig(
            strategy="invalid",
        )
