import asyncio
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from app.config import settings
from app.utils.url_validator import validate_public_url

USER_AGENT = "LinkScopeAI/0.1 (website analysis; assessment project)"

RELEVANT_PATH_HINTS = ("about", "service", "product", "solution", "contact", "company")

def _extract_page(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "iframe", "nav", "footer"]):
        tag.decompose()
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    description = ""
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        description = meta["content"].strip()
    headings = [h.get_text(" ", strip=True) for h in soup.find_all(["h1", "h2", "h3"])]
    main = soup.find("main") or soup.find("article") or soup.body or soup
    text = " ".join(main.stripped_strings)
    text = " ".join(text.split())
    links = []
    for a in soup.find_all("a", href=True):
        absolute = urljoin(url, a["href"])
        parsed = urlparse(absolute)
        if parsed.scheme in ("http", "https") and parsed.netloc == urlparse(url).netloc:
            label = a.get_text(" ", strip=True)
            if label:
                links.append({"url": absolute, "text": label[:100]})
    return {"url": url, "title": title, "meta_description": description,
            "headings": headings[:40], "text": text[:settings.max_content_chars],
            "internal_links": links[:100]}

def _choose_pages(home: dict, base_url: str, max_pages: int) -> list[str]:
    scored = []
    seen = {base_url.rstrip("/")}
    for link in home["internal_links"]:
        url = link["url"].split("#")[0].rstrip("/")
        if url in seen:
            continue
        path = urlparse(url).path.lower()
        label = link["text"].lower()
        if any(hint in path or hint in label for hint in RELEVANT_PATH_HINTS):
            scored.append(url)
            seen.add(url)
    return scored[:max(0, max_pages - 1)]

async def _fetch(client: httpx.AsyncClient, url: str) -> dict:
    # Validate before each fetch to reduce SSRF risk.
    validate_public_url(url)
    response = await client.get(url, follow_redirects=False)
    if response.status_code in (301, 302, 303, 307, 308):
        location = response.headers.get("location")
        if not location:
            raise ValueError(f"Website redirected without a Location header: {url}")
        redirected = urljoin(url, location)
        validate_public_url(redirected)
        response = await client.get(redirected, follow_redirects=False)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type and "application/xhtml" not in content_type:
        raise ValueError(f"URL did not return HTML content: {url}")
    return _extract_page(response.text, str(response.url))

async def extract_website(url: str) -> list[dict]:
    validate_public_url(url)
    timeout = httpx.Timeout(settings.request_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout, headers={"User-Agent": USER_AGENT}) as client:
        home = await _fetch(client, url)
        candidate_pages = _choose_pages(home, url, settings.max_pages)
        pages = [home]
        if candidate_pages:
            results = await asyncio.gather(
                *[_fetch(client, page_url) for page_url in candidate_pages],
                return_exceptions=True,
            )
            for result in results:
                if isinstance(result, dict):
                    pages.append(result)
    # Bound total text, not just each page.
    remaining = settings.max_content_chars
    for page in pages:
        page["text"] = page["text"][:remaining]
        remaining -= len(page["text"])
        if remaining <= 0:
            break
    return pages
