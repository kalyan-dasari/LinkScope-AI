from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Enable CORS for public API deployment and cross-origin consumer access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
