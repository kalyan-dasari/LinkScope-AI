import pytest
from app.utils.url_validator import validate_public_url

def test_rejects_localhost():
    with pytest.raises(ValueError):
        validate_public_url("http://localhost")

def test_rejects_private_ip():
    with pytest.raises(ValueError):
        validate_public_url("http://192.168.1.1")

def test_rejects_non_http_scheme():
    with pytest.raises(ValueError):
        validate_public_url("ftp://example.com")
