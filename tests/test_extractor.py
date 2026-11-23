from app.services.website_extractor import _choose_pages, _extract_page

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Acme AI &mdash; Autonomous Agents</title>
    <meta name="description" content="Acme builds next-generation enterprise agentic workflows.">
</head>
<body>
    <nav><a href="/pricing">Pricing</a></nav>
    <main>
        <h1>Next Gen AI</h1>
        <h2>Enterprise Workflows</h2>
        <p>We provide automated workflow orchestration and AI agent solutions for engineering teams.</p>
        <a href="https://example.com/about">About Us</a>
        <a href="https://example.com/services">Our Services</a>
        <a href="https://other.com/external">External Link</a>
    </main>
    <script>console.log("ignore me");</script>
    <footer>Copyright 2026</footer>
</body>
</html>
"""

def test_extract_page():
    page = _extract_page(SAMPLE_HTML, "https://example.com")
    assert "Acme AI" in page["title"]
    assert "next-generation enterprise" in page["meta_description"]
    assert "Next Gen AI" in page["headings"]
    assert "Enterprise Workflows" in page["headings"]
    assert "automated workflow orchestration" in page["text"]
    assert "ignore me" not in page["text"]
    assert "Copyright 2026" not in page["text"]

    # Verify only internal links were retained
    urls = [link["url"] for link in page["internal_links"]]
    assert "https://example.com/about" in urls
    assert "https://example.com/services" in urls
    assert "https://other.com/external" not in urls

def test_choose_pages():
    home = {
        "internal_links": [
            {"url": "https://example.com/about", "text": "About"},
            {"url": "https://example.com/services", "text": "Services"},
            {"url": "https://example.com/terms", "text": "Terms of Service"},
            {"url": "https://example.com/blog/article-1", "text": "Read more"},
        ]
    }
    candidates = _choose_pages(home, "https://example.com", max_pages=3)
    # Max pages is 3, home is 1, so up to 2 candidates chosen
    assert len(candidates) <= 2
    assert "https://example.com/about" in candidates
    assert "https://example.com/services" in candidates

def test_ssrf_safe_backend_blocks_private_ip():
    import anyio
    import pytest
    from app.services.website_extractor import SSRFSafeBackend
    from app.exceptions import InvalidUrlError

    backend = SSRFSafeBackend()

    async def _check():
        with pytest.raises(InvalidUrlError):
            await backend.connect_tcp("127.0.0.1", 80)
        with pytest.raises(InvalidUrlError):
            await backend.connect_tcp("169.254.169.254", 80)

    anyio.run(_check)
