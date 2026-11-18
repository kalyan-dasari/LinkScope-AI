import time
from app.services.website_extractor import extract_website
from app.services.llm_service import analyze_content
from app.schemas import LinkAnalysisResponse, Metadata

async def analyze_website(url: str) -> LinkAnalysisResponse:
    start = time.perf_counter()
    try:
        pages = await extract_website(url)
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Unable to fetch or extract website content: {type(exc).__name__}") from exc

    combined_text = " ".join(page.get("text", "") for page in pages).strip()
    if len(combined_text) < 100:
        raise ValueError("The website did not provide enough readable content to analyze.")

    context = {
        "website": url,
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
    try:
        payload = await __run_llm(context)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"LLM analysis failed: {type(exc).__name__}") from exc

    elapsed = round(time.perf_counter() - start, 2)
    from app.config import settings
    return LinkAnalysisResponse(
        success=True,
        website=url,
        brand=payload.brand,
        analysis=payload.analysis,
        metadata=Metadata(
            pages_analyzed=len(pages),
            analysis_model=settings.gemini_model,
            processing_time_seconds=elapsed,
        ),
    )

async def __run_llm(context: dict):
    # Gemini SDK call is synchronous; run in a worker thread to avoid blocking the event loop.
    import asyncio
    return await asyncio.to_thread(analyze_content, context)
