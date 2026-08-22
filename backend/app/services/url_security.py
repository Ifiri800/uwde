from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


class URLSecurityError(ValueError):
    """Raised when a URL is unsafe for server-side fetching."""


BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
    "metadata",
}


BLOCKED_IPS = {
    ipaddress.ip_address("169.254.169.254"),
    ipaddress.ip_address("100.100.100.200"),
}


def validate_url(url: str) -> str:
    """
    Validate a user-provided URL before the server makes a network request.

    Returns the normalized URL when it passes validation.
    Raises URLSecurityError when the URL is unsafe.
    """

    parsed = urlparse(url)

    if parsed.scheme.lower() not in {"http", "https"}:
        raise URLSecurityError("Only HTTP and HTTPS URLs are allowed.")

    if not parsed.hostname:
        raise URLSecurityError("The URL must contain a hostname.")

    hostname = parsed.hostname.rstrip(".").lower()

    if hostname in BLOCKED_HOSTNAMES:
        raise URLSecurityError("This hostname is not allowed.")

    try:
        addresses = socket.getaddrinfo(
            hostname,
            parsed.port or (443 if parsed.scheme.lower() == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise URLSecurityError("The hostname could not be resolved.") from exc

    resolved_ips = {
        ipaddress.ip_address(address[4][0])
        for address in addresses
    }

    for ip in resolved_ips:
        if ip in BLOCKED_IPS:
            raise URLSecurityError("This destination is not allowed.")

        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise URLSecurityError(
                "The URL resolves to a non-public network address."
            )

    return parsed.geturl()