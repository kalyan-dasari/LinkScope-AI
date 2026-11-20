import asyncio
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from app.config import settings
from app.exceptions import InvalidUrlError, WebsiteInaccessibleError
from app.utils.url_validator import validate_public_url

USER_AGENT = "LinkScopeAI/0.1 (website analysis; assessment project)"
RELEVANT_PATH_HINTS = (
    "about",
    "service",
    "product",
    "solution",
    "industr",
    "contact",
    "company",
    "pricing",
    "feature",
)

def _extract_page(html: str, url: str) -> dict:
    """Safely parses HTML, strips boilerplate, and extracts semantic textual data."""
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception as exc:
        # Graceful handling for malformed HTML
        soup = BeautifulSoup("", "html.parser")

    for tag in soup(["script", "style", "noscript", "svg", "iframe", "nav", "footer", "form", "button"]):
        tag.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    description = ""
    meta = (
        soup.find("meta", attrs={"name": "description"})
        or soup.find("meta", attrs={"property": "og:description"})
        or soup.find("meta", attrs={"name": "twitter:description"})
    )
    if meta and meta.get("content"):
        description = meta["content"].strip()

    headings = [h.get_text(" ", strip=True) for h in soup.find_all(["h1", "h2", "h3"]) if h.get_text(strip=True)]

    # Prioritize main semantic content block
    main = soup.find("main") or soup.find("article") or soup.body or soup
    body_text = " ".join(main.stripped_strings) if main else ""
    body_text = " ".join(body_text.split())

    # Build comprehensive textual content: combine metadata and body text.
    # This ensures modern SPAs (React/Vue/Vite) with empty body shells but rich
    # titles and meta descriptions can still be understood and analyzed.
    content_blocks = []
    if title:
        content_blocks.append(f"Title: {title}")
    if description:
        content_blocks.append(f"Meta Description: {description}")
    if headings:
        content_blocks.append("Headings: " + " | ".join(headings))
    if body_text:
        content_blocks.append(body_text)

    combined_text = "\n".join(content_blocks) if content_blocks else body_text

    links = []
    base_netloc = urlparse(url).netloc.lower()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        absolute = urljoin(url, href)
        parsed = urlparse(absolute)
        if parsed.scheme in ("http", "https") and parsed.netloc.lower() == base_netloc:
            label = a.get_text(" ", strip=True)
            if label:
                links.append({"url": absolute, "text": label[:100]})

    return {
        "url": url,
        "title": title,
        "meta_description": description,
        "headings": headings[:40],
        "text": combined_text[:settings.max_content_chars],
        "internal_links": links[:100],
    }

def _choose_pages(home: dict, base_url: str, max_pages: int) -> list[str]:
    """Scores and selects the most relevant internal subpages for deeper domain understanding."""
    scored = []
    seen = {base_url.rstrip("/")}
    for link in home.get("internal_links", []):
        raw_url = link["url"].split("#")[0].rstrip("/")
        if raw_url in seen:
            continue
        path = urlparse(raw_url).path.lower()
        label = link.get("text", "").lower()
        if any(hint in path or hint in label for hint in RELEVANT_PATH_HINTS):
            scored.append(raw_url)
            seen.add(raw_url)
    return scored[:max(0, max_pages - 1)]

async def _fetch(client: httpx.AsyncClient, target_url: str) -> dict:
    """
    Fetches a webpage with multi-hop redirect verification, stream-bounded size limits,
    and granular HTTP error differentiation.
    """
    current_url = target_url
    hops = 0
    visited_urls = set()
    max_hops = settings.max_redirects
    max_bytes = settings.max_response_bytes

    while hops < max_hops:
        validate_public_url(current_url)
        visited_urls.add(current_url)

        try:
            async with client.stream("GET", current_url, follow_redirects=False) as response:
                # Handle HTTP redirects with per-hop SSRF validation
                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("location")
                    if not location:
                        raise WebsiteInaccessibleError(f"Target '{current_url}' redirected without a Location header.")

                    next_url = urljoin(current_url, location)
                    if next_url in visited_urls:
                        raise WebsiteInaccessibleError(f"Circular redirect detected targeting '{next_url}'.")

                    current_url = next_url
                    hops += 1
                    continue

                if response.status_code == 403:
                    raise WebsiteInaccessibleError(
                        f"Access to '{current_url}' was forbidden (HTTP 403). The website may block automated crawlers or use anti-bot gates."
                    )
                if response.status_code == 404:
                    raise WebsiteInaccessibleError(
                        f"Target website returned HTTP 404 Not Found for '{current_url}'."
                    )
                if response.status_code >= 400:
                    raise WebsiteInaccessibleError(
                        f"Target website returned HTTP {response.status_code} ({response.reason_phrase}) for '{current_url}'."
                    )

                content_type = response.headers.get("content-type", "").lower()
                if "text/html" not in content_type and "application/xhtml" not in content_type:
                    raise WebsiteInaccessibleError(
                        f"URL did not return HTML content (Content-Type: '{content_type}'): {current_url}"
                    )

                # Stream and read chunks up to maximum allowed bytes
                chunks = []
                total_bytes = 0
                async for chunk in response.aiter_bytes():
                    total_bytes += len(chunk)
                    if total_bytes > max_bytes:
                        raise WebsiteInaccessibleError(
                            f"Target webpage exceeds maximum allowed size ({max_bytes // (1024*1024)}MB): {current_url}"
                        )
                    chunks.append(chunk)

                raw_body = b"".join(chunks)
                encoding = response.encoding or "utf-8"
                html_text = raw_body.decode(encoding, errors="replace")
                return _extract_page(html_text, str(response.url))

        except (httpx.TimeoutException, TimeoutError) as exc:
            raise WebsiteInaccessibleError(
                f"Connection to '{current_url}' timed out after {settings.request_timeout_seconds}s."
            ) from exc
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            raise WebsiteInaccessibleError(
                f"Failed to connect to '{current_url}': Host unreachable or network connection refused."
            ) from exc
        except (InvalidUrlError, WebsiteInaccessibleError):
            raise
        except Exception as exc:
            raise WebsiteInaccessibleError(
                f"Unexpected error while fetching '{current_url}': {type(exc).__name__} - {exc}"
            ) from exc

    raise WebsiteInaccessibleError(f"Exceeded maximum redirect limit ({max_hops} hops) for URL: {target_url}")

async def extract_website(url: str) -> list[dict]:
    """
    Crawls the homepage and up to (settings.max_pages - 1) relevant internal pages.
    Bounds total content length to settings.max_content_chars.
    """
    validate_public_url(url)
    timeout = httpx.Timeout(settings.request_timeout_seconds)
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)

    async with httpx.AsyncClient(timeout=timeout, limits=limits, headers={"User-Agent": USER_AGENT}) as client:
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

    # Bound total combined text length
    remaining = settings.max_content_chars
    for page in pages:
        page["text"] = page["text"][:remaining]
        remaining -= len(page["text"])
        if remaining <= 0:
            break

    return pages
