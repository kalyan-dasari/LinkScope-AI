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

# Standard public web ports allowed for public link analysis
ALLOWED_PORTS = {80, 443, 8080, 8443}

FORBIDDEN_IPV4_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),          # Current network (RFC 1122)
    ipaddress.ip_network("10.0.0.0/8"),         # Private-use (RFC 1918)
    ipaddress.ip_network("100.64.0.0/10"),      # Shared Address Space / CGNAT (RFC 6598)
    ipaddress.ip_network("127.0.0.0/8"),        # Loopback (RFC 1122)
    ipaddress.ip_network("169.254.0.0/16"),     # Link-local / Cloud metadata (RFC 3927)
    ipaddress.ip_network("172.16.0.0/12"),      # Private-use (RFC 1918)
    ipaddress.ip_network("192.0.0.0/24"),       # IETF Protocol Assignments (RFC 6890)
    ipaddress.ip_network("192.0.2.0/24"),       # Documentation / TEST-NET-1 (RFC 5737)
    ipaddress.ip_network("192.168.0.0/16"),     # Private-use (RFC 1918)
    ipaddress.ip_network("198.18.0.0/15"),      # Benchmarking (RFC 2544)
    ipaddress.ip_network("198.51.100.0/24"),    # Documentation / TEST-NET-2 (RFC 5737)
    ipaddress.ip_network("203.0.113.0/24"),     # Documentation / TEST-NET-3 (RFC 5737)
    ipaddress.ip_network("224.0.0.0/4"),        # Multicast (RFC 5771)
    ipaddress.ip_network("240.0.0.0/4"),        # Reserved (RFC 1112)
    ipaddress.ip_network("255.255.255.255/32"), # Limited Broadcast (RFC 919)
    ipaddress.ip_network("100.100.100.200/32"), # Alibaba Cloud metadata
]

FORBIDDEN_IPV6_NETWORKS = [
    ipaddress.ip_network("::/128"),             # Unspecified
    ipaddress.ip_network("::1/128"),           # Loopback
    ipaddress.ip_network("::ffff:0:0/96"),      # IPv4-mapped IPv6
    ipaddress.ip_network("64:ff9b::/96"),       # IPv4/IPv6 translation
    ipaddress.ip_network("100::/64"),           # Discard prefix
    ipaddress.ip_network("2001:db8::/32"),      # Documentation
    ipaddress.ip_network("fc00::/7"),           # Unique Local (ULA)
    ipaddress.ip_network("fe80::/10"),          # Link-Local Unicast
    ipaddress.ip_network("ff00::/8"),           # Multicast
]

def _is_ip_public(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Verify that an IP address is genuinely global, public, and not reserved or cloud metadata."""
    if ip.is_unspecified or ip.is_loopback or ip.is_link_local or ip.is_private or ip.is_reserved or ip.is_multicast:
        return False
    if not ip.is_global:
        return False

    # Check against explicit IPv4 forbidden ranges
    if isinstance(ip, ipaddress.IPv4Address):
        for net in FORBIDDEN_IPV4_NETWORKS:
            if ip in net:
                return False

    # Check against explicit IPv6 forbidden ranges
    if isinstance(ip, ipaddress.IPv6Address):
        # Handle IPv4-mapped IPv6 addresses (e.g. ::ffff:127.0.0.1)
        if ip.ipv4_mapped:
            return _is_ip_public(ip.ipv4_mapped)
        for net in FORBIDDEN_IPV6_NETWORKS:
            if ip in net:
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
        raise InvalidUrlError(
            f"Port {parsed.port} is not supported. Use standard web ports (80, 443, 8080, 8443)."
        )

    # Check if hostname is an IP address literal (IPv4 or IPv6)
    try:
        ip = ipaddress.ip_address(hostname)
        if not _is_ip_public(ip):
            raise InvalidUrlError("Private, loopback, link-local, or cloud metadata IP addresses are not allowed.")
        return
    except ValueError as exc:
        if "not allowed" in str(exc):
            raise
        # If ValueError, hostname is a domain name; proceed to DNS resolution

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
