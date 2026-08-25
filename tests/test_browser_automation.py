import sys
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "backend"),
)

from backend.app.services.browser_automation import BrowserAutomation


@pytest.fixture
def browser():
    service = BrowserAutomation()

    service.start()

    yield service

    service.close()


def test_browser_starts(browser):
    assert browser._browser is not None


def test_opens_javascript_page(browser):
    page = browser.open_page(
        "data:text/html,"
        "<html><body>"
        "<h1>Hello UWDE</h1>"
        "</body></html>"
    )

    assert page.title == ""
    assert "Hello UWDE" in page.html
    assert "Hello UWDE" in page.text


def test_returns_final_url(browser):
    page = browser.open_page(
        "data:text/html,"
        "<html><body>"
        "<h1>UWDE</h1>"
        "</body></html>"
    )

    assert page.url.startswith("data:text/html")


def test_serializes_browser_page(browser):
    page = browser.open_page(
        "data:text/html,"
        "<html><body>"
        "<h1>UWDE</h1>"
        "</body></html>"
    )

    data = page.to_dict()

    assert "url" in data
    assert "title" in data
    assert "html" in data
    assert "text" in data


def test_rejects_empty_url(browser):
    with pytest.raises(ValueError):
        browser.open_page("")


def test_rejects_invalid_timeout():
    with pytest.raises(ValueError):
        BrowserAutomation(timeout_ms=0)


def test_context_manager():
    with BrowserAutomation() as browser:
        assert browser._browser is not None

    assert browser._browser is None
