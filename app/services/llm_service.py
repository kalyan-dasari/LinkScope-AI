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
            if exc.code == 429:
                raise LLMServiceError(f"Gemini API quota exceeded or rate limit hit (HTTP 429): {exc.message}") from exc
            raise LLMServiceError(f"Gemini API request failed (HTTP {exc.code}): {exc.message}") from exc
        except (TimeoutError, TimeoutException if "TimeoutException" in globals() else TimeoutError) as exc:
            raise LLMServiceError(f"Gemini API request timed out: {exc}") from exc
        except Exception as exc:
            raise LLMServiceError(f"LLM provider error ({type(exc).__name__}): {exc}") from exc

        raw_text = response.text or ""
        if not raw_text.strip():
            raise LLMServiceError("The LLM returned an empty response.")

        try:
            return AnalysisPayload.model_validate_json(raw_text)
        except Exception as exc:
            raise LLMServiceError(f"LLM output failed schema validation: {exc}") from exc

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
            prompt = build_analysis_prompt(site_context)
            schema_json = json.dumps(AnalysisPayload.model_json_schema())
            system_msg = (
                f"{prompt}\n\n"
                f"CONCISENESS REQUIREMENT:\n"
                f"Be crisp, factual, and concise. Keep bullet points, summaries, and descriptions to 1-2 punchy sentences. "
                f"Avoid verbose fluff. Ensure all 5 sections are populated completely within token bounds.\n\n"
                f"STRICT SCHEMA REQUIREMENTS:\n"
                f"You MUST return a JSON object with top-level keys 'brand' and 'analysis'.\n"
                f"'analysis' MUST contain ALL FIVE sections:\n"
                f"  1. 'competitor_analysis' (brand_overview, business_model, competitors, strengths, weaknesses, gaps, advantages, opportunities)\n"
                f"  2. 'target_search_queries' (EXACTLY 5 query objects with query, platforms, intent, business_relevance, target_audience)\n"
                f"  3. 'seo_improvements' (primary_keyword, secondary_keywords, long_tail_keywords, recommended_title, meta_description, etc.)\n"
                f"  4. 'top_services' (between 1 and 5 service objects with name, description, target_industry, target_customer, main_benefit, source)\n"
                f"  5. 'target_audience' (primary_audience, secondary_audience, industry_segments, business_types, customer_profiles, etc.)\n\n"
                f"JSON Schema:\n{schema_json}"
            )

            completion = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {
                        "role": "user",
                        "content": (
                            "Analyze the website crawl evidence and produce the complete JSON report. "
                            "Ensure none of the 5 analysis sections are omitted."
                        ),
                    },
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=3000,
            )
        except Exception as exc:
            raise LLMServiceError(f"Groq API request failed ({type(exc).__name__}): {exc}") from exc

        raw_text = completion.choices[0].message.content or ""
        if not raw_text.strip():
            raise LLMServiceError("Groq returned an empty response.")

        try:
            return AnalysisPayload.model_validate_json(raw_text)
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
