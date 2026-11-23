from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routes.analysis import router as analysis_router

app = FastAPI(
    title="LinkScope AI",
    description=(
        "Production-grade, AI-powered website analysis API. Extracts website content with HTTPX and "
        "BeautifulSoup, guards against SSRF, and leverages Google Gemini 2.0 Flash for structured "
        "competitor intelligence, search queries, SEO audit, and audience segmentation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Standard secure CORS configuration for public API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """Maps client request format validation errors to HTTP 400 Bad Request."""
    errors = exc.errors()
    error_msg = errors[0].get("msg", "Invalid request body") if errors else "Invalid request body"
    field_loc = errors[0].get("loc", ["request"])[-1] if errors else "request"
    return JSONResponse(
        status_code=400,
        content={"detail": f"Invalid {field_loc}: {error_msg}"},
    )

app.include_router(analysis_router)

@app.get("/", tags=["General"], summary="API Root & Links")
async def root():
    return {
        "name": "LinkScope AI",
        "description": "AI-powered website, competitor, SEO, and audience analysis API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health_check": "/health",
        "analysis_endpoint": "POST /link-analysis",
    }

@app.get("/health", tags=["General"], summary="Service Health Probe")
async def health():
    return {"status": "ok", "service": "LinkScope AI"}
