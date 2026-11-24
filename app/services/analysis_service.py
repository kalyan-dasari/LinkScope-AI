import asyncio
import time
from app.config import settings
from app.exceptions import (
    ContentTooShortError,
    InvalidUrlError,
    LLMConfigError,
    LLMServiceError,
    WebsiteInaccessibleError,
)
from app.schemas import LinkAnalysisResponse, Metadata
from app.services.llm_service import analyze_content
from app.services.website_extractor import extract_website

async def analyze_website(url: str) -> LinkAnalysisResponse:
    """
    Coordinates extraction of website pages and LLM-driven structured analysis.
    Offloads synchronous LLM calls to a background thread to keep the async event loop responsive.
    """
    start_time = time.perf_counter()

    # Step 1: Fetch and extract website pages
    pages = await extract_website(url)

    # Step 2: Validate extracted content volume
    combined_text = " ".join(page.get("text", "") for page in pages).strip()
    if len(combined_text) < 50:
        raise ContentTooShortError(
            f"The website at '{url}' did not provide sufficient readable text ({len(combined_text)} characters extracted). "
            "It may be heavily JavaScript-dependent, password-protected, or empty."
        )

    # Step 3: Package extracted context for LLM prompt
    context = {
        "website": url,
        "pages_analyzed_count": len(pages),
        "pages": [
            {
                "url": page["url"],
                "title": page["title"],
                "meta_description": page["meta_description"],
                "headings": page["headings"],
                "content": page["text"],
            }
            for page in pages
        ],
    }

    # Step 4: Run AI analysis in worker thread
    payload = await asyncio.to_thread(analyze_content, context)

    # Step 5: Construct validated response with telemetry
    elapsed_seconds = round(time.perf_counter() - start_time, 2)
    return LinkAnalysisResponse(
        success=True,
        website=url,
        brand=payload.brand,
        analysis=payload.analysis,
        metadata=Metadata(
            pages_analyzed=len(pages),
            analysis_model=settings.active_model,
            processing_time_seconds=elapsed_seconds,
        ),
    )
