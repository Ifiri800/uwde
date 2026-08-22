import pytest

from backend.app.services.pagination import (
    PaginationConfig,
    PaginationStrategy,
    build_next_url,
    detect_pagination,
)


def test_detects_next_page_link():
    html = """
    <html>
        <body>
            <a href="/jobs?page=2" rel="next">Next</a>
        </body>
    </html>
    """

    result = detect_pagination(
        html,
        "https://example.com/jobs?page=1",
    )

    assert result.strategy == PaginationStrategy.NEXT_LINK
    assert result.next_url == "https://example.com/jobs?page=2"


def test_detects_numbered_url_pagination():
    result = build_next_url(
        "https://example.com/jobs?page=1",
        PaginationConfig(
            strategy=PaginationStrategy.URL,
            parameter="page",
        ),
        page_number=2,
    )

    assert result == "https://example.com/jobs?page=2"


def test_preserves_existing_query_parameters():
    result = build_next_url(
        "https://example.com/jobs?category=environment&page=1",
        PaginationConfig(
            strategy=PaginationStrategy.URL,
            parameter="page",
        ),
        page_number=2,
    )

    assert result == "https://example.com/jobs?category=environment&page=2"


def test_supports_custom_page_parameter():
    result = build_next_url(
        "https://example.com/jobs?pg=1",
        PaginationConfig(
            strategy=PaginationStrategy.URL,
            parameter="pg",
        ),
        page_number=3,
    )

    assert result == "https://example.com/jobs?pg=3"


def test_respects_max_pages():
    config = PaginationConfig(
        strategy=PaginationStrategy.URL,
        parameter="page",
        max_pages=3,
    )

    assert config.max_pages == 3


def test_respects_max_records():
    config = PaginationConfig(
        strategy=PaginationStrategy.URL,
        parameter="page",
        max_records=100,
    )

    assert config.max_records == 100


def test_detects_load_more_button():
    html = """
    <html>
        <body>
            <button id="load-more">Load More</button>
        </body>
    </html>
    """

    result = detect_pagination(
        html,
        "https://example.com/jobs",
    )

    assert result.strategy == PaginationStrategy.LOAD_MORE


def test_detects_infinite_scroll_hint():
    html = """
    <html>
        <body>
            <div data-infinite-scroll="true">
                Job results
            </div>
        </body>
    </html>
    """

    result = detect_pagination(
        html,
        "https://example.com/jobs",
    )

    assert result.strategy == PaginationStrategy.INFINITE_SCROLL


def test_returns_none_when_no_pagination_detected():
    html = """
    <html>
        <body>
            <article>Only one page</article>
        </body>
    </html>
    """

    result = detect_pagination(
        html,
        "https://example.com/jobs",
    )

    assert result.strategy == PaginationStrategy.NONE
    assert result.next_url is None


def test_rejects_invalid_max_pages():
    with pytest.raises(ValueError):
        PaginationConfig(
            strategy=PaginationStrategy.URL,
            parameter="page",
            max_pages=0,
        )


def test_rejects_invalid_max_records():
    with pytest.raises(ValueError):
        PaginationConfig(
            strategy=PaginationStrategy.URL,
            parameter="page",
            max_records=0,
        )
