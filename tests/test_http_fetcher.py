import httpx
import pytest

from backend.app.services.http_fetcher import (
    FetchError,
    fetch_url,
)


def mock_response(
    status_code=200,
    *,
    content=b"<html><h1>Hello</h1></html>",
    headers=None,
    url="https://example.com",
):
    return httpx.Response(
        status_code=status_code,
        headers=headers or {"content-type": "text/html; charset=utf-8"},
        content=content,
        request=httpx.Request("GET", url),
    )


def test_fetches_html(monkeypatch):
    response = mock_response()

    def fake_get(self, url):
        return response

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    result = fetch_url("https://example.com")

    assert result.status_code == 200
    assert result.content_type.startswith("text/html")
    assert result.body == b"<html><h1>Hello</h1></html>"
    assert result.final_url == "https://example.com"


def test_rejects_unsafe_initial_url():
    with pytest.raises(FetchError):
        fetch_url("http://127.0.0.1")


def test_rejects_non_html_content(monkeypatch):
    response = mock_response(
        headers={"content-type": "application/pdf"},
    )

    def fake_get(self, url):
        return response

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    with pytest.raises(FetchError, match="Unsupported content type"):
        fetch_url("https://example.com/file.pdf")


def test_rejects_http_errors(monkeypatch):
    response = mock_response(404)

    def fake_get(self, url):
        return response

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    with pytest.raises(FetchError, match="HTTP 404"):
        fetch_url("https://example.com/missing")


def test_follows_safe_redirect(monkeypatch):
    redirect = mock_response(
        302,
        headers={
            "location": "https://example.com/page2",
        },
        url="https://example.com",
    )

    final = mock_response(
        200,
        content=b"<html><h1>Page 2</h1></html>",
        url="https://example.com/page2",
    )

    responses = iter([redirect, final])

    def fake_get(self, url):
        return next(responses)

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    result = fetch_url("https://example.com")

    assert result.status_code == 200
    assert result.final_url == "https://example.com/page2"
    assert result.body == b"<html><h1>Page 2</h1></html>"


def test_blocks_unsafe_redirect(monkeypatch):
    redirect = mock_response(
        302,
        headers={
            "location": "http://127.0.0.1/admin",
        },
        url="https://example.com",
    )

    def fake_get(self, url):
        return redirect

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    with pytest.raises(FetchError, match="Unsafe redirect"):
        fetch_url("https://example.com")


def test_blocks_too_many_redirects(monkeypatch):
    redirect = mock_response(
        302,
        headers={
            "location": "https://example.com/next",
        },
        url="https://example.com",
    )

    def fake_get(self, url):
        return redirect

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    with pytest.raises(FetchError, match="Too many redirects"):
        fetch_url("https://example.com")


def test_rejects_oversized_response(monkeypatch):
    large_body = b"x" * 100

    response = mock_response(
        content=large_body,
        headers={
            "content-type": "text/html",
            "content-length": "100",
        },
    )

    def fake_get(self, url):
        return response

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    with pytest.raises(FetchError, match="larger than"):
        fetch_url(
            "https://example.com",
            max_response_size=50,
        )


def test_handles_timeout(monkeypatch):
    def fake_get(self, url):
        raise httpx.ReadTimeout(
            "Request timed out",
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    with pytest.raises(FetchError, match="timed out"):
        fetch_url("https://example.com")