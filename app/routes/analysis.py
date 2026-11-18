from fastapi import APIRouter, HTTPException
from app.schemas import LinkAnalysisRequest, LinkAnalysisResponse
from app.services.analysis_service import analyze_website

router = APIRouter(tags=["Link Analysis"])

@router.post("/link-analysis", response_model=LinkAnalysisResponse)
async def link_analysis(payload: LinkAnalysisRequest):
    try:
        return await analyze_website(str(payload.url))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        # Avoid leaking stack traces or secrets to clients.
        raise HTTPException(status_code=500, detail="Analysis failed unexpectedly. Please try again.") from exc
