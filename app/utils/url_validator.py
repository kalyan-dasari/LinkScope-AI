import ipaddress
import socket
from urllib.parse import urlparse
from app.exceptions import InvalidUrlError

DISALLOWED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
    "instance-data",
}

# Standard web ports allowed for public link analysis
ALLOWED_PORTS = {80, 443, 8000, 8080, 8443}

def _is_ip_public(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Verify that an IP address is genuinely global and not internal/reserved."""
    if not ip.is_global:
        return False
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
        return False
    # Explicitly block cloud metadata service IPv4 link-local range (169.254.0.0/16)
    if isinstance(ip, ipaddress.IPv4Address) and ip in ipaddress.ip_network("169.254.0.0/16"):
        return False
    return True

def validate_public_url(url: str) -> None:
    """
    Validate that a given URL is a safe, public HTTP/HTTPS URL.
    Defends against Server-Side Request Forgery (SSRF) and invalid URL formats.
    """
    if not url or not isinstance(url, str):
        raise InvalidUrlError("A valid URL string is required.")

    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        raise InvalidUrlError("Only http and https protocols are supported.")
    
    if not parsed.hostname:
        raise InvalidUrlError("URL must contain a valid hostname.")
    
    # Reject credentials in URL (e.g. http://user:pass@hostname)
    if parsed.username or parsed.password:
        raise InvalidUrlError("URLs containing user credentials are not allowed.")

    hostname = parsed.hostname.lower().strip(".")
    if hostname in DISALLOWED_HOSTNAMES or hostname.endswith(".local") or hostname.endswith(".internal"):
        raise InvalidUrlError(f"Target host '{hostname}' is not allowed.")

    # Validate port if specified
    if parsed.port and parsed.port not in ALLOWED_PORTS:
        raise InvalidUrlError(f"Port {parsed.port} is not supported. Use standard web ports (80, 443, 8080, 8443).")

    # Reject literal IPs that are not public
    try:
        ip = ipaddress.ip_address(hostname)
        if not _is_ip_public(ip):
            raise InvalidUrlError("Private, loopback, link-local, or cloud metadata IP addresses are not allowed.")
        return
    except ValueError as exc:
        if "not allowed" in str(exc):
            raise
        # If ValueError is from ipaddress parsing, hostname is a domain name, proceed to DNS resolution

    # DNS resolution check: resolve and verify all returned addresses
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        infos = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise InvalidUrlError(f"Hostname '{hostname}' could not be resolved.") from exc
    except Exception as exc:
        raise InvalidUrlError(f"Failed to resolve hostname '{hostname}': {exc}") from exc

    addresses = {info[4][0] for info in infos}
    if not addresses:
        raise InvalidUrlError(f"Hostname '{hostname}' did not resolve to any IP address.")

    for address in addresses:
        try:
            ip_obj = ipaddress.ip_address(address)
            if not _is_ip_public(ip_obj):
                raise InvalidUrlError(f"Hostname '{hostname}' resolves to a non-public IP address.")
        except ValueError:
            raise InvalidUrlError(f"Hostname '{hostname}' resolved to an invalid address: {address}")
