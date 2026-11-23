from fastapi import APIRouter, HTTPException, status
from app.exceptions import (
    ContentTooShortError,
    InvalidUrlError,
    LLMConfigError,
    LLMServiceError,
    WebsiteInaccessibleError,
)
from app.schemas import ErrorResponse, LinkAnalysisRequest, LinkAnalysisResponse
from app.services.analysis_service import analyze_website

from app.utils.url_validator import validate_public_url

HTTP_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)

router = APIRouter(tags=["Link Analysis"])

@router.post(
    "/link-analysis",
    response_model=LinkAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze website for SEO, competitors, services, and audience",
    description=(
        "Crawls the supplied website, extracts content using HTTPX and BeautifulSoup, "
        "and produces a comprehensive AI-powered business and SEO intelligence report via Gemini."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Invalid URL scheme, missing host, or private/SSRF target.",
        },
        HTTP_422: {
            "model": ErrorResponse,
            "description": "Insufficient readable text extracted from website (< 100 characters).",
        },
        status.HTTP_502_BAD_GATEWAY: {
            "model": ErrorResponse,
            "description": "Target website was unreachable, timed out, or LLM generation failed.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "LLM API Key is missing or service is not configured.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected internal server failure.",
        },
    },
)
async def link_analysis(payload: LinkAnalysisRequest):
    """Analyze a public website URL."""
    try:
        url_str = payload.url.strip() if isinstance(payload.url, str) else str(payload.url)
        validate_public_url(url_str)
        return await analyze_website(url_str)
    except InvalidUrlError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ContentTooShortError as exc:
        raise HTTPException(status_code=HTTP_422, detail=str(exc)) from exc
    except WebsiteInaccessibleError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except LLMConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except LLMServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except Exception as exc:
        # Prevent stack trace leakage in public environments
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal error occurred during analysis. Please try again later.",
        ) from exc
