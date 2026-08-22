import pytest

from backend.app.services.url_security import (
    URLSecurityError,
    validate_url,
)


def test_allows_public_https_url():
    result = validate_url("https://example.com")
    assert result == "https://example.com"


def test_allows_public_http_url():
    result = validate_url("http://example.com")
    assert result == "http://example.com"


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com",
        "javascript:alert(1)",
        "data:text/plain,hello",
    ],
)
def test_rejects_unsafe_protocols(url):
    with pytest.raises(URLSecurityError):
        validate_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost",
        "http://localhost.localdomain",
        "http://127.0.0.1",
        "http://169.254.169.254",
    ],
)
def test_rejects_local_and_metadata_hosts(url):
    with pytest.raises(URLSecurityError):
        validate_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://10.0.0.1",
        "http://172.16.0.1",
        "http://192.168.1.1",
    ],
)
def test_rejects_private_networks(url):
    with pytest.raises(URLSecurityError):
        validate_url(url)


def test_rejects_missing_hostname():
    with pytest.raises(URLSecurityError):
        validate_url("https://")


def test_rejects_non_http_scheme():
    with pytest.raises(URLSecurityError):
        validate_url("ssh://example.com")