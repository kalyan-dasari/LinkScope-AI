from unittest.mock import MagicMock, patch
import pytest
from app.exceptions import LLMConfigError
from app.schemas import (
    AnalysisPayload,
    AnalysisSections,
    BrandInfo,
    CompetitorAnalysis,
    SEOImprovements,
    SearchQuery,
    ServiceInsight,
    TargetAudience,
)
from app.services.llm_service import analyze_content, get_llm_provider, GeminiProvider, GroqProvider

def _generate_valid_payload():
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
    brand = BrandInfo(name="TestBrand", category="AI", summary="AI platform", source="website_content")
    comp_analysis = CompetitorAnalysis(
        brand_overview="Leading provider",
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
    sections = AnalysisSections(
        competitor_analysis=comp_analysis,
        target_search_queries=[dummy_query] * 5,
        seo_improvements=seo,
        top_services=[dummy_service],
        target_audience=audience,
    )
    return AnalysisPayload(brand=brand, analysis=sections)

def test_analyze_content_raises_when_no_api_key():
    with patch("app.services.llm_service.settings.gemini_api_key", ""):
        with patch("app.services.llm_service.settings.groq_api_key", ""):
            with pytest.raises(LLMConfigError):
                analyze_content({"website": "https://example.com", "pages": []})

def test_analyze_content_success_with_mocked_gemini():
    payload_obj = _generate_valid_payload()
    json_str = payload_obj.model_dump_json()

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json_str
    mock_client.models.generate_content.return_value = mock_response

    with patch("app.services.llm_service.settings.gemini_api_key", "mock_key"):
        with patch("app.services.llm_service.genai.Client", return_value=mock_client):
            result = analyze_content({"website": "https://example.com", "pages": []})
            assert result.brand.name == "TestBrand"
            assert len(result.analysis.target_search_queries) == 5
            assert result.analysis.seo_improvements.primary_keyword == "ai agents"

def test_analyze_content_success_with_mocked_groq():
    payload_obj = _generate_valid_payload()
    json_str = payload_obj.model_dump_json()

    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = json_str
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_completion

    with patch("app.services.llm_service.settings.llm_provider", "groq"):
        with patch("app.services.llm_service.settings.groq_api_key", "gsk_mock_groq_key"):
            with patch("groq.Groq", return_value=mock_client):
                provider = get_llm_provider()
                assert isinstance(provider, GroqProvider)
                result = provider.analyze({"website": "https://example.com", "pages": []})
                assert result.brand.name == "TestBrand"
                assert len(result.analysis.target_search_queries) == 5
