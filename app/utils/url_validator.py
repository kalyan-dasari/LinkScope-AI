import ipaddress
import socket
from urllib.parse import urlparse

def validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only http and https URLs are supported.")
    if not parsed.hostname:
        raise ValueError("URL must contain a hostname.")
    hostname = parsed.hostname.lower().strip(".")
    if hostname in ("localhost", "localhost.localdomain"):
        raise ValueError("Localhost URLs are not allowed.")

    # Reject literal IPs that are not public.
    try:
        ip = ipaddress.ip_address(hostname)
        if not ip.is_global:
            raise ValueError("Private, loopback, reserved, or non-public IPs are not allowed.")
    except ValueError as exc:
        # If the error is from ipaddress parsing, it's a hostname, not a blocked IP.
        if "not allowed" in str(exc):
            raise
    else:
        return

    # DNS resolution check: reject if any resolved address is non-public.
    try:
        infos = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80),
                                  type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError("Hostname could not be resolved.") from exc
    addresses = {info[4][0] for info in infos}
    if not addresses:
        raise ValueError("Hostname did not resolve to an IP address.")
    for address in addresses:
        if not ipaddress.ip_address(address).is_global:
            raise ValueError("Hostname resolves to a private or non-public IP address.")
