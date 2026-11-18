import asyncio
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from app.config import settings
from app.exceptions import InvalidUrlError, WebsiteInaccessibleError
from app.utils.url_validator import validate_public_url

USER_AGENT = "LinkScopeAI/0.1 (website analysis; assessment project)"
MAX_REDIRECT_HOPS = 5
MAX_RESPONSE_BYTES = 2 * 1024 * 1024  # 2 MB safety cap per page
RELEVANT_PATH_HINTS = ("about", "service", "product", "solution", "contact", "company", "pricing", "feature")

def _extract_page(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "iframe", "nav", "footer", "form"]):
        tag.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    description = ""
    meta = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
    if meta and meta.get("content"):
        description = meta["content"].strip()

    headings = [h.get_text(" ", strip=True) for h in soup.find_all(["h1", "h2", "h3"]) if h.get_text(strip=True)]
    
    # Priority on main semantic content container if available
    main = soup.find("main") or soup.find("article") or soup.body or soup
    text = " ".join(main.stripped_strings)
    text = " ".join(text.split())

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
        "text": text[:settings.max_content_chars],
        "internal_links": links[:100],
    }

def _choose_pages(home: dict, base_url: str, max_pages: int) -> list[str]:
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
    current_url = target_url
    hops = 0
    visited_urls = set()

    while hops < MAX_REDIRECT_HOPS:
        validate_public_url(current_url)
        visited_urls.add(current_url)

        try:
            # Stream response to enforce size limits before allocating memory
            async with client.stream("GET", current_url, follow_redirects=False) as response:
                # Handle redirect status codes with SSRF verification on every hop
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

                if response.status_code >= 400:
                    raise WebsiteInaccessibleError(
                        f"Target website returned HTTP {response.status_code} ({response.reason_phrase}) for '{current_url}'."
                    )

                content_type = response.headers.get("content-type", "").lower()
                if "text/html" not in content_type and "application/xhtml" not in content_type:
                    raise WebsiteInaccessibleError(f"URL did not return HTML content (Content-Type: '{content_type}'): {current_url}")

                # Read body in chunks up to MAX_RESPONSE_BYTES
                chunks = []
                total_bytes = 0
                async for chunk in response.aiter_bytes():
                    total_bytes += len(chunk)
                    if total_bytes > MAX_RESPONSE_BYTES:
                        raise WebsiteInaccessibleError(
                            f"Target webpage exceeds maximum allowed size ({MAX_RESPONSE_BYTES // (1024*1024)}MB): {current_url}"
                        )
                    chunks.append(chunk)

                raw_body = b"".join(chunks)
                # Decode using response encoding or fallback to utf-8
                encoding = response.encoding or "utf-8"
                html_text = raw_body.decode(encoding, errors="replace")
                return _extract_page(html_text, str(response.url))

        except (httpx.TimeoutException, TimeoutError) as exc:
            raise WebsiteInaccessibleError(f"Connection to '{current_url}' timed out after {settings.request_timeout_seconds}s.") from exc
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            raise WebsiteInaccessibleError(f"Failed to connect to '{current_url}': Network or host unreachable.") from exc
        except (InvalidUrlError, WebsiteInaccessibleError):
            raise
        except Exception as exc:
            raise WebsiteInaccessibleError(f"Unexpected error while fetching '{current_url}': {type(exc).__name__} - {exc}") from exc

    raise WebsiteInaccessibleError(f"Exceeded maximum redirect limit ({MAX_REDIRECT_HOPS} hops) for URL: {target_url}")

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

    # Bound total text across all retrieved pages
    remaining = settings.max_content_chars
    for page in pages:
        page["text"] = page["text"][:remaining]
        remaining -= len(page["text"])
        if remaining <= 0:
            break
            
    return pages
