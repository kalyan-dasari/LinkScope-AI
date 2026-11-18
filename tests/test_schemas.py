import pytest
from pydantic import ValidationError
from app.schemas import (
    AnalysisPayload,
    AnalysisSections,
    BrandInfo,
    CompetitorAnalysis,
    LinkAnalysisRequest,
    SEOImprovements,
    SearchQuery,
    ServiceInsight,
    TargetAudience,
)

def test_link_analysis_request_valid():
    req = LinkAnalysisRequest(url="https://stripe.com")
    assert str(req.url) == "https://stripe.com/"

def test_link_analysis_request_invalid_scheme():
    with pytest.raises(ValidationError):
        LinkAnalysisRequest(url="ftp://stripe.com")

def test_search_queries_must_be_five():
    dummy_query = SearchQuery(
        query="ai orchestration platform",
        platforms=["Google", "LinkedIn"],
        intent="Commercial",
        business_relevance="High purchase intent",
        target_audience="CTOs and Tech Leads",
    )
    dummy_service = ServiceInsight(
        name="AI Automation",
        description="Enterprise workflow automation",
        target_industry=["Tech", "Finance"],
        target_customer=["Engineering leaders"],
        main_benefit="Reduces manual dev effort by 80%",
        source="website",
    )
    brand = BrandInfo(name="TestBrand", category="AI", summary="AI platform")
    comp_analysis = CompetitorAnalysis(
        brand_overview="Overview",
        competitors=[],
        brand_strengths=["Fast", "Accurate"],
        competitive_advantages=["Proprietary algorithms"],
        opportunities=["Expansion to APAC"],
    )
    seo = SEOImprovements(
        primary_keyword="ai agents",
        secondary_keywords=["workflow automation"],
        long_tail_keywords=["enterprise ai agent framework"],
        recommended_title="AI Agent Automation Framework",
        meta_description="Enterprise-grade AI agent orchestration platform.",
        supporting_content=["Agent architectures guide"],
    )
    audience = TargetAudience(
        primary_audience=["CTOs"],
        secondary_audience=["Software Engineers"],
        industries=["SaaS"],
        business_types=["B2B"],
        customer_profiles=["Technical Decision Makers"],
        geographical_focus=["Global"],
        customer_needs=["Fast agent development"],
        interests=["AI", "Python"],
        marketing_segments=["Cloud software"],
    )

    # Only 4 queries -> should raise ValidationError because min_length=5
    with pytest.raises(ValidationError):
        AnalysisSections(
            competitor_analysis=comp_analysis,
            target_search_queries=[dummy_query] * 4,
            seo_improvements=seo,
            top_services=[dummy_service],
            target_audience=audience,
        )

    # Exactly 5 queries -> valid
    sections = AnalysisSections(
        competitor_analysis=comp_analysis,
        target_search_queries=[dummy_query] * 5,
        seo_improvements=seo,
        top_services=[dummy_service],
        target_audience=audience,
    )
    payload = AnalysisPayload(brand=brand, analysis=sections)
    assert len(payload.analysis.target_search_queries) == 5
