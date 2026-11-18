from google import genai
from google.genai import types
from google.genai.errors import APIError
from app.config import settings
from app.exceptions import LLMConfigError, LLMServiceError
from app.prompts.analysis_prompt import build_analysis_prompt
from app.schemas import AnalysisPayload

def analyze_content(site_context: dict) -> AnalysisPayload:
    """
    Submits extracted website content to Gemini API for structured intelligence extraction.
    Uses native JSON schema enforcement via Google GenAI SDK.
    """
    if not settings.gemini_api_key or settings.gemini_api_key == "replace_with_your_key":
        raise LLMConfigError("GEMINI_API_KEY is not configured. Please provide a valid Gemini API key in your .env file.")

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        prompt = build_analysis_prompt(site_context)

        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AnalysisPayload,
                temperature=0.2,
            ),
        )
    except APIError as exc:
        raise LLMServiceError(f"Gemini API request failed (HTTP {exc.code}): {exc.message}") from exc
    except Exception as exc:
        raise LLMServiceError(f"Failed to communicate with LLM provider: {type(exc).__name__} - {exc}") from exc

    raw_text = response.text or ""
    if not raw_text.strip():
        raise LLMServiceError("The LLM returned an empty response.")

    try:
        return AnalysisPayload.model_validate_json(raw_text)
    except Exception as exc:
        raise LLMServiceError(f"LLM response failed schema validation: {exc}") from exc
