from fastapi import FastAPI
from app.routes.analysis import router as analysis_router

app = FastAPI(
    title="LinkScope AI",
    description="AI-powered website, competitor, SEO, service, and audience analysis API.",
    version="0.1.0",
)

app.include_router(analysis_router)

@app.get("/", tags=["General"])
async def root():
    return {
        "name": "LinkScope AI",
        "description": "Website link analysis API",
        "docs": "/docs",
        "health": "/health",
    }

@app.get("/health", tags=["General"])
async def health():
    return {"status": "ok"}
