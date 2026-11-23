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

def test_prompt_spec_field_aliases_and_root_fields():
    """Verify that all assessment prompt schema aliases and root-level fields are synchronized."""
    from app.schemas import LinkAnalysisResponse, Metadata

    dummy_query = SearchQuery(
        query="custom website development services",
        platforms=["Google Search", "LinkedIn", "X (Twitter)"],
        intent="Service Search",
        business_relevance="Lead generation for agencies",
        target_audience="Small Business Owners",
    )
    dummy_service = ServiceInsight(
        name="Full-Stack Web Development",
        description="End-to-end custom responsive web applications",
        target_industry=["SaaS", "E-commerce"],
        target_customer=["Founders"],
        main_benefit="Faster time to market",
        source="extracted",
    )
    brand = BrandInfo(name="ABC Technologies", category="Technology Services", summary="Digital agency")
    comp_analysis = CompetitorAnalysis(
        brand_name="ABC Technologies",
        industry_category="Technology Services",
        brand_overview="A technology company providing digital solutions.",
        brand_strengths=["Affordable Solutions", "Quick turnaround"],
        competitive_advantages=["Proprietary tooling"],
        opportunities=["Improve Online Visibility"],
    )
    seo = SEOImprovements(
        primary_keyword="Technology Services",
        secondary_keywords=["Web Development", "Cloud Solutions"],
        recommended_title="ABC Technologies - Premier Technology Services",
        meta_description="A technology company providing digital solutions and software development.",
        supporting_content=["Service landing pages", "Industry FAQs"],
    )
    audience = TargetAudience(
        primary_audience=["Small Businesses", "Startups"],
        secondary_audience=["Marketing Managers"],
        industries=["Technology", "Retail"],
        business_types=["SMB", "Enterprise Companies"],
        customer_needs=["Website Development", "Online Presence"],
    )
    sections = AnalysisSections(
        competitor_analysis=comp_analysis,
        target_search_queries=[dummy_query] * 5,
        seo_improvements=seo,
        top_services=[dummy_service],
        target_audience=audience,
    )

    resp = LinkAnalysisResponse(
        website="https://example.com/",
        brand=brand,
        analysis=sections,
        metadata=Metadata(pages_analyzed=1, analysis_model="gemini-2.0-flash", processing_time_seconds=1.2),
    )

    # 1. Section 1 aliases
    assert resp.analysis.competitor_analysis.strengths == ["Affordable Solutions", "Quick turnaround"]
    assert resp.analysis.competitor_analysis.business_overview == "A technology company providing digital solutions."
    assert resp.analysis.competitor_analysis.main_business_category == "Technology Services"
    assert resp.analysis.competitor_analysis.opportunities_to_improve_market_positioning == ["Improve Online Visibility"]

    # 2. Section 2 aliases
    first_q = resp.analysis.target_search_queries[0]
    assert first_q.search_intent == "Service Search"
    assert first_q.platform == "Google Search"
    assert first_q.relevant_platform == "Google Search"

    # 3. Section 3 aliases
    assert resp.analysis.seo_improvements.supporting_content == ["Service landing pages", "Industry FAQs"]
    assert resp.analysis.seo_improvements.content_recommendations == ["Service landing pages", "Industry FAQs"]
    assert resp.analysis.seo_improvements.recommended_seo_title == "ABC Technologies - Premier Technology Services"

    # 4. Section 4 aliases
    assert resp.analysis.top_services[0].service_name == "Full-Stack Web Development"

    # 5. Section 5 aliases
    assert resp.analysis.target_audience.industries == ["Technology", "Retail"]
    assert resp.analysis.target_audience.primary_target_audience == ["Small Businesses", "Startups"]

    # 6. Direct root-level section fields
    assert resp.competitor_analysis is not None
    assert resp.target_search_queries is not None
    assert resp.seo_improvements is not None
    assert resp.seo_recommendations is not None
    assert resp.top_services is not None
    assert resp.target_audience is not None
