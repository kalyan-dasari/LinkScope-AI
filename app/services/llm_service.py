from abc import ABC, abstractmethod
import json
from google import genai
from google.genai import types
from google.genai.errors import APIError
from app.config import settings
from app.exceptions import LLMConfigError, LLMServiceError
from app.prompts.analysis_prompt import build_analysis_prompt
from app.schemas import AnalysisPayload

class BaseLLMProvider(ABC):
    """Abstract interface for LLM analysis providers."""

    @abstractmethod
    def analyze(self, site_context: dict) -> AnalysisPayload:
        """Process website crawl evidence and return validated analysis payload."""
        pass

class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider utilizing native JSON schema enforcement."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.gemini_api_key
        self.model = model or settings.gemini_model

    def analyze(self, site_context: dict) -> AnalysisPayload:
        if not self.api_key or self.api_key.strip() in ("", "replace_with_your_key"):
            raise LLMConfigError(
                "GEMINI_API_KEY is not configured. Please supply a valid Gemini API key in your .env file."
            )

        try:
            client = genai.Client(api_key=self.api_key)
            prompt = build_analysis_prompt(site_context)

            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AnalysisPayload,
                    temperature=0.2,
                ),
            )
        except APIError as exc:
            code = getattr(exc, "code", None) or 500
            msg = getattr(exc, "message", None) or str(exc)
            if code == 429:
                raise LLMServiceError(f"Gemini API quota exceeded or rate limit hit (HTTP 429): {msg}") from exc
            raise LLMServiceError(f"Gemini API request failed (HTTP {code}): {msg}") from exc
        except TimeoutError as exc:
            raise LLMServiceError(f"Gemini API request timed out: {exc}") from exc
        except Exception as exc:
            if "Timeout" in type(exc).__name__:
                raise LLMServiceError(f"Gemini API request timed out: {exc}") from exc
            raise LLMServiceError(f"LLM provider error ({type(exc).__name__}): {exc}") from exc

        raw_text = response.text or ""
        if not raw_text.strip():
            raise LLMServiceError("The LLM returned an empty response.")

        try:
            payload = AnalysisPayload.model_validate_json(raw_text)
            if not payload.analysis.competitor_analysis.brand_name:
                payload.analysis.competitor_analysis.brand_name = payload.brand.name
            if not payload.analysis.competitor_analysis.industry_category:
                payload.analysis.competitor_analysis.industry_category = payload.brand.category
            return payload
        except Exception as exc:
            raise LLMServiceError(f"LLM output failed schema validation: {exc}") from exc

GROQ_SCHEMA_SKELETON = """{
  "brand": {
    "name": "Brand Name",
    "category": "Market Category",
    "summary": "Concise 1-2 sentence brand summary",
    "source": "website_content"
  },
  "analysis": {
    "competitor_analysis": {
      "brand_overview": "Overview of brand positioning",
      "business_model": "e.g. Marketplace, B2B SaaS, Agency",
      "main_products_or_services": ["Product/Service 1", "Product/Service 2"],
      "competitors": [
        {
          "name": "Competitor 1",
          "website": "https://example.com",
          "description": "Core offering",
          "strengths": ["Strength 1"],
          "weaknesses": ["Weakness 1"],
          "verification_status": "ai_suggested",
          "notes": "Positioning overlap"
        },
        {
          "name": "Competitor 2",
          "website": "https://example.com",
          "description": "Core offering",
          "strengths": ["Strength 1"],
          "weaknesses": ["Weakness 1"],
          "verification_status": "ai_suggested",
          "notes": "Positioning overlap"
        },
        {
          "name": "Competitor 3",
          "website": "https://example.com",
          "description": "Core offering",
          "strengths": ["Strength 1"],
          "weaknesses": ["Weakness 1"],
          "verification_status": "ai_suggested",
          "notes": "Positioning overlap"
        }
      ],
      "brand_strengths": ["Strength 1"],
      "brand_weaknesses": ["Weakness 1"],
      "competitive_gaps": ["Gap 1"],
      "competitive_advantages": ["Advantage 1"],
      "opportunities": ["Opportunity 1"]
    },
    "target_search_queries": [
      {"query": "Query 1", "platforms": ["Google"], "intent": "Commercial", "business_relevance": "Relevance", "target_audience": "Audience persona"},
      {"query": "Query 2", "platforms": ["Google"], "intent": "Informational", "business_relevance": "Relevance", "target_audience": "Audience persona"},
      {"query": "Query 3", "platforms": ["Google"], "intent": "Transactional", "business_relevance": "Relevance", "target_audience": "Audience persona"},
      {"query": "Query 4", "platforms": ["LinkedIn"], "intent": "Commercial", "business_relevance": "Relevance", "target_audience": "Audience persona"},
      {"query": "Query 5", "platforms": ["Google"], "intent": "Navigational", "business_relevance": "Relevance", "target_audience": "Audience persona"}
    ],
    "seo_improvements": {
      "primary_keyword": "Primary keyword",
      "secondary_keywords": ["Secondary keyword 1"],
      "long_tail_keywords": ["Long tail phrase 1"],
      "business_related_keywords": ["Industry keyword 1"],
      "recommended_title": "Optimized HTML Title (50-60 chars)",
      "meta_description": "Optimized Meta Description (140-160 chars)",
      "content_recommendations": ["Content recommendation 1"],
      "on_page_improvements": ["On-page improvement 1"],
      "technical_seo_suggestions": ["Technical suggestion 1"]
    },
    "top_services": [
      {
        "name": "Service Name",
        "description": "Detailed description",
        "target_industry": ["Industry 1"],
        "target_customer": ["Customer persona 1"],
        "main_benefit": "Key ROI or benefit",
        "source": "extracted"
      }
    ],
    "target_audience": {
      "primary_audience": ["Primary decision-makers"],
      "secondary_audience": ["Secondary users/evaluators"],
      "industry_segments": ["Segment 1"],
      "business_types": ["B2B / B2C"],
      "customer_profiles": ["Profile 1"],
      "geographic_markets": ["Global / Regional"],
      "customer_needs": ["Need 1"],
      "customer_interests": ["Interest 1"],
      "marketing_segments": ["Segment 1"],
      "targeting_opportunities": ["Opportunity 1"],
      "source_classification": "inferred"
    }
  }
}"""

def _format_groq_evidence(site_context: dict, max_hp_chars: int = 4000, max_sub_chars: int = 1500) -> str:
    target_url = site_context.get("website") or site_context.get("base_url") or ""
    parts = [f"TARGET WEBSITE: {target_url}"]

    pages = site_context.get("pages", [])
    if pages:
        hp = pages[0]
        parts.append("\n--- HOMEPAGE EVIDENCE ---")
        if hp.get("title"):
            parts.append(f"Title: {hp['title']}")
        if hp.get("meta_description"):
            parts.append(f"Meta Description: {hp['meta_description']}")
        if hp.get("headings"):
            parts.append(f"Headings: {' | '.join(hp['headings'][:10])}")
        content = hp.get("content") or hp.get("text") or ""
        if content:
            parts.append(f"Content:\n{content[:max_hp_chars]}")

        subpages = pages[1:]
        if subpages:
            parts.append(f"\n--- INTERNAL SUBPAGES ({len(subpages)} pages) ---")
            for i, sp in enumerate(subpages[:3], 1):
                parts.append(f"\nSubpage {i} ({sp.get('url')}):")
                if sp.get("title"):
                    parts.append(f"Title: {sp['title']}")
                if sp.get("headings"):
                    parts.append(f"Headings: {' | '.join(sp['headings'][:6])}")
                sp_content = sp.get("content") or sp.get("text") or ""
                if sp_content:
                    parts.append(f"Content: {sp_content[:max_sub_chars]}")
    else:
        hp = site_context.get("homepage", {})
        parts.append("\n--- HOMEPAGE EVIDENCE ---")
        if hp.get("title"):
            parts.append(f"Title: {hp['title']}")
        if hp.get("meta_description"):
            parts.append(f"Meta Description: {hp['meta_description']}")
        if hp.get("headings"):
            parts.append(f"Headings: {' | '.join(hp['headings'][:10])}")
        content = hp.get("content") or hp.get("text") or ""
        if content:
            parts.append(f"Content:\n{content[:max_hp_chars]}")

    return "\n".join(parts)

class GroqProvider(BaseLLMProvider):
    """Groq LPU provider running high-speed models (e.g. openai/gpt-oss-120b)."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.groq_api_key
        self.model = model or settings.groq_model

    def analyze(self, site_context: dict) -> AnalysisPayload:
        if not self.api_key or self.api_key.strip() in ("", "replace_with_your_key"):
            raise LLMConfigError(
                "GROQ_API_KEY is not configured. Please supply a valid Groq API key in your .env file."
            )

        try:
            from groq import Groq
            client = Groq(api_key=self.api_key)
            evidence_summary = _format_groq_evidence(site_context)

            prompt = (
                "You are a Senior Website Business Analyst, SEO Strategist, and Competitive Intelligence Expert.\n"
                "Analyze the website evidence below and generate a complete, rigorous, and assessment-grade JSON report.\n\n"
                f"{evidence_summary}\n\n"
                "CRITICAL REQUIREMENTS:\n"
                "1. competitor_analysis: brand_overview, business_model, at least 3 relevant competitors (direct/indirect) "
                "with strengths, weaknesses, verification_status ('verified' if confirmed on site, otherwise 'ai_suggested'), "
                "brand_strengths, brand_weaknesses, competitive_gaps, competitive_advantages, opportunities.\n"
                "2. target_search_queries: EXACTLY 5 search query objects (query, platforms, intent, business_relevance, target_audience).\n"
                "3. seo_improvements: primary_keyword, secondary_keywords, long_tail_keywords, business_related_keywords, "
                "recommended_title, meta_description, content_recommendations, on_page_improvements, technical_seo_suggestions.\n"
                "4. top_services: 1 to 5 core services (name, description, target_industry, target_customer, main_benefit, source).\n"
                "5. target_audience: primary_audience, secondary_audience, industry_segments, business_types, customer_profiles, "
                "geographic_markets, customer_needs, customer_interests, marketing_segments, targeting_opportunities, source_classification.\n"
                "6. Keep summaries, descriptions, and bullet points concise (1-2 sentences each). Do NOT omit any section.\n\n"
                f"Adhere strictly to this JSON structure:\n{GROQ_SCHEMA_SKELETON}"
            )

            completion = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=3500,
            )
        except Exception as exc:
            raise LLMServiceError(f"Groq API request failed ({type(exc).__name__}): {exc}") from exc

        raw_text = completion.choices[0].message.content or ""
        if not raw_text.strip():
            raise LLMServiceError("Groq returned an empty response.")

        try:
            payload = AnalysisPayload.model_validate_json(raw_text)
            if not payload.analysis.competitor_analysis.brand_name:
                payload.analysis.competitor_analysis.brand_name = payload.brand.name
            if not payload.analysis.competitor_analysis.industry_category:
                payload.analysis.competitor_analysis.industry_category = payload.brand.category
            return payload
        except Exception as exc:
            raise LLMServiceError(f"Groq LLM output failed schema validation: {exc}") from exc

def get_llm_provider() -> BaseLLMProvider:
    """Factory to instantiate the active LLM provider."""
    provider_name = settings.active_provider
    if provider_name == "gemini":
        return GeminiProvider()
    elif provider_name == "groq":
        return GroqProvider()
    raise LLMConfigError(f"Unsupported LLM provider '{provider_name}'. Supported providers: gemini, groq")

def analyze_content(site_context: dict) -> AnalysisPayload:
    """Convenience entry point using the active LLM provider."""
    provider = get_llm_provider()
    return provider.analyze(site_context)
