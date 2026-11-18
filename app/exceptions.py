"""Custom domain exceptions for LinkScope AI."""

class LinkScopeError(Exception):
    """Base exception for all LinkScope domain errors."""
    pass

class InvalidUrlError(LinkScopeError, ValueError):
    """Raised when a URL is malformed, uses an unsupported scheme, or targets a private/internal address (SSRF)."""
    pass

class WebsiteInaccessibleError(LinkScopeError, RuntimeError):
    """Raised when the target website cannot be reached, times out, returns an HTTP error, or is blocked."""
    pass

class ContentTooShortError(LinkScopeError, ValueError):
    """Raised when the extracted content has less readable text than the minimum required threshold."""
    pass

class LLMConfigError(LinkScopeError, RuntimeError):
    """Raised when the Gemini API key or model configuration is missing or invalid."""
    pass

class LLMServiceError(LinkScopeError, RuntimeError):
    """Raised when the Gemini API call fails, times out, rate limits, or returns unparseable output."""
    pass
