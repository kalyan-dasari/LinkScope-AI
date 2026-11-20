from abc import ABC, abstractmethod
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
            # Handle rate-limit / quota errors distinctly
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

def get_llm_provider() -> BaseLLMProvider:
    """Factory to instantiate the configured LLM provider."""
    provider_name = settings.llm_provider.lower().strip()
    if provider_name == "gemini":
        return GeminiProvider()
    raise LLMConfigError(f"Unsupported LLM provider '{provider_name}'. Supported providers: gemini")

def analyze_content(site_context: dict) -> AnalysisPayload:
    """Convenience entry point using the active LLM provider."""
    provider = get_llm_provider()
    return provider.analyze(site_context)
