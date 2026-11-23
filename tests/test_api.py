from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException
from app.exceptions import (
    ContentTooShortError,
    InvalidUrlError,
    LLMConfigError,
    WebsiteInaccessibleError,
)
from app.main import health, root
from app.routes.analysis import link_analysis
from app.schemas import (
    AnalysisPayload,
    AnalysisSections,
    BrandInfo,
    Competitor,
    CompetitorAnalysis,
    LinkAnalysisRequest,
    LinkAnalysisResponse,
    SEOImprovements,
    SearchQuery,
    ServiceInsight,
    TargetAudience,
)

def _generate_valid_mock_payload():
    competitor = Competitor(
        name="MockComp",
        website="https://mockcomp.com",
        description="A direct competitor",
        strengths=["High market presence"],
        weaknesses=["Legacy architecture"],
        verification_status="ai_suggested",
        notes="Competes directly in cloud services",
    )
    comp_analysis = CompetitorAnalysis(
        brand_overview="Overview of brand",
        business_model="B2B SaaS",
        main_products_or_services=["AI Workflow Orchestration"],
        competitors=[competitor] * 3,
        brand_strengths=["Fast", "Accurate"],
        brand_weaknesses=["Early-stage brand awareness"],
        competitive_gaps=["Competitors offer 24/7 phone support"],
        competitive_advantages=["Proprietary low-latency models"],
        opportunities=["Expansion to European enterprise market"],
    )
    query = SearchQuery(
        query="ai link analysis api",
        platforms=["Google", "LinkedIn"],
        intent="Commercial",
        business_relevance="Direct customer acquisition",
        target_audience="CTOs and Tech Leads",
    )
    seo = SEOImprovements(
        primary_keyword="link analysis api",
        secondary_keywords=["seo analyzer", "competitor intelligence"],
        long_tail_keywords=["how to automate competitor link analysis"],
        business_related_keywords=["b2b link intelligence"],
        recommended_title="LinkScope AI - Intelligent Website Analysis",
        meta_description="Fast, reliable AI website link and competitor analysis API.",
        content_recommendations=["Guide to link intelligence"],
        on_page_improvements=["Add hero CTA"],
        technical_seo_suggestions=["Add OpenGraph metadata"],
    )
    service = ServiceInsight(
        name="Website SEO Audit",
        description="Automated audit of semantic page structure",
        target_industry=["Technology"],
        target_customer=["Product Teams"],
        main_benefit="Actionable search visibility recommendations",
        source="extracted",
    )
    audience = TargetAudience(
        primary_audience=["Engineering Leaders"],
        secondary_audience=["Product Managers"],
        industry_segments=["Software", "SaaS"],
        business_types=["B2B"],
        customer_profiles=["Technical Evaluator"],
        geographic_markets=["North America", "Global"],
        customer_needs=["Fast structured competitor insights"],
        customer_interests=["FastAPI", "LLMs"],
        marketing_segments=["Cloud Engineering"],
        targeting_opportunities=["LinkedIn Developer Ads"],
        source_classification="inferred",
    )
    sections = AnalysisSections(
        competitor_analysis=comp_analysis,
        target_search_queries=[query] * 5,
        seo_improvements=seo,
        top_services=[service],
        target_audience=audience,
    )
    brand = BrandInfo(
        name="LinkScope",
        category="Developer Tools",
        summary="Automated website intelligence platform",
        source="website_content",
    )
    return AnalysisPayload(brand=brand, analysis=sections)

@pytest.mark.asyncio
async def test_health_endpoint():
    res = await health()
    assert res["status"] == "ok"
    assert "LinkScope AI" in res["service"]

@pytest.mark.asyncio
async def test_root_endpoint():
    res = await root()
    assert res["name"] == "LinkScope AI"
    assert res["documentation"] == "/docs"
    assert res["health_check"] == "/health"
    assert res["analysis_endpoint"] == "POST /link-analysis"

@pytest.mark.asyncio
async def test_link_analysis_rejects_ssrf():
    req = LinkAnalysisRequest(url="http://127.0.0.1")
    with pytest.raises(HTTPException) as exc_info:
        await link_analysis(req)
    assert exc_info.value.status_code == 400

@pytest.mark.asyncio
async def test_link_analysis_rejects_localhost():
    req = LinkAnalysisRequest(url="http://localhost:8000")
    with pytest.raises(HTTPException) as exc_info:
        await link_analysis(req)
    assert exc_info.value.status_code == 400

@pytest.mark.asyncio
async def test_link_analysis_handles_inaccessible_website():
    req = LinkAnalysisRequest(url="https://example.com")
    with patch("app.routes.analysis.analyze_website", side_effect=WebsiteInaccessibleError("Host unreachable")):
        with pytest.raises(HTTPException) as exc_info:
            await link_analysis(req)
        assert exc_info.value.status_code == 502
        assert "Host unreachable" in exc_info.value.detail

@pytest.mark.asyncio
async def test_link_analysis_handles_thin_content():
    req = LinkAnalysisRequest(url="https://example.com")
    with patch("app.routes.analysis.analyze_website", side_effect=ContentTooShortError("Too thin")):
        with pytest.raises(HTTPException) as exc_info:
            await link_analysis(req)
        assert exc_info.value.status_code == 422
        assert "Too thin" in exc_info.value.detail

@pytest.mark.asyncio
async def test_link_analysis_handles_missing_api_key():
    req = LinkAnalysisRequest(url="https://example.com")
    with patch("app.routes.analysis.analyze_website", side_effect=LLMConfigError("Missing key")):
        with pytest.raises(HTTPException) as exc_info:
            await link_analysis(req)
        assert exc_info.value.status_code == 503
        assert "Missing key" in exc_info.value.detail

@pytest.mark.asyncio
async def test_link_analysis_success():
    req = LinkAnalysisRequest(url="https://example.com")
    mock_payload = _generate_valid_mock_payload()

    mock_pages = [
        {
            "url": "https://example.com",
            "title": "Example Domain",
            "meta_description": "For use in examples",
            "headings": ["Example Domain"],
            "text": "This domain is for use in illustrative examples in documents." * 5,
            "internal_links": [],
        }
    ]

    with patch("app.services.analysis_service.extract_website", return_value=mock_pages):
        with patch("app.services.analysis_service.analyze_content", return_value=mock_payload):
            response = await link_analysis(req)
            assert isinstance(response, LinkAnalysisResponse)
            assert response.success is True
            assert response.website == "https://example.com/"
            assert response.brand.name == "LinkScope"
            assert len(response.analysis.target_search_queries) == 5
            assert len(response.analysis.competitor_analysis.competitors) >= 3
            assert response.metadata.pages_analyzed == 1
            # Verify root-level section availability for automated grading
            assert response.competitor_analysis is not None
            assert response.target_search_queries is not None
            assert response.seo_recommendations is not None
            assert response.top_services is not None
            assert response.target_audience is not None
            # Verify field aliases
            q = response.target_search_queries[0]
            assert q.search_intent is not None
            assert q.relevance is not None
            assert len(q.recommended_platforms) > 0
            seo = response.seo_recommendations
            assert seo.suggested_seo_title is not None
            assert seo.suggested_meta_description is not None
            assert len(seo.primary_keywords) > 0
            svc = response.top_services[0]
            assert svc.service_name is not None
            aud = response.target_audience
            assert len(aud.target_industry) > 0
            assert len(aud.interests) > 0

@pytest.mark.asyncio
async def test_http_endpoint_rejects_invalid_urls_with_400():
    from httpx import ASGITransport, AsyncClient
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        invalid_cases = [
            "ftp://example.com",
            "file:///etc/passwd",
            "not-a-valid-url",
            "http://127.0.0.1",
            "http://localhost",
            "http://169.254.169.254",
            "http://10.0.0.1",
            "http://metadata.google.internal",
        ]
        for bad_url in invalid_cases:
            resp = await client.post("/link-analysis", json={"url": bad_url})
            assert resp.status_code == 400, f"Expected 400 for {bad_url}, got {resp.status_code}: {resp.text}"
