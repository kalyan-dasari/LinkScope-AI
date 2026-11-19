import pytest
from app.exceptions import InvalidUrlError
from app.utils.url_validator import validate_public_url

def test_rejects_localhost():
    with pytest.raises(InvalidUrlError):
        validate_public_url("http://localhost")
 
def test_rejects_localhost_ip():
    with pytest.raises(InvalidUrlError):
        validate_public_url("http://127.0.0.1")

def test_rejects_private_ip():
    with pytest.raises(InvalidUrlError):
        validate_public_url("http://192.168.1.1")

def test_rejects_cloud_metadata_ip():
    with pytest.raises(InvalidUrlError):
        validate_public_url("http://169.254.169.254")

def test_rejects_metadata_domain():
    with pytest.raises(InvalidUrlError):
        validate_public_url("http://metadata.google.internal")

def test_rejects_non_http_scheme():
    with pytest.raises(InvalidUrlError):
        validate_public_url("ftp://example.com")
    with pytest.raises(InvalidUrlError):
        validate_public_url("file:///etc/passwd")

def test_rejects_credentials_in_url():
    with pytest.raises(InvalidUrlError):
        validate_public_url("http://admin:secret@example.com")

def test_rejects_dangerous_ports():
    with pytest.raises(InvalidUrlError):
        validate_public_url("http://example.com:22")
    with pytest.raises(InvalidUrlError):
        validate_public_url("http://example.com:3306")
