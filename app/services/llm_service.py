import json
from google import genai
from google.genai import types
from app.config import settings
from app.schemas import AnalysisPayload

def analyze_content(site_context: dict) -> AnalysisPayload:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured. Add it to your .env file.")

    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = f"""You are a careful website business, competitor, SEO, and marketing analyst.
Analyze ONLY the supplied website evidence. Distinguish explicit evidence from inference.
Do not invent facts, search volumes, rankings, traffic, revenue, or verified competitor claims.
Competitors may be suggested from general knowledge, but label verification_status as ai_suggested
unless their details are independently verified in the supplied evidence. If uncertain, use unknown.
Services should be sourced from website content when possible; mark inferred services as inferred.
Provide exactly 5 target search queries. Include relevant platforms from Google, Facebook,
Instagram, LinkedIn, and X. Generate practical, specific recommendations.
Return brand and all analysis sections matching the provided schema.

WEBSITE EVIDENCE:
{json.dumps(site_context, ensure_ascii=False)}
"""
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AnalysisPayload,
            temperature=0.2,
        ),
    )
    try:
        return AnalysisPayload.model_validate_json(response.text or "")
    except Exception as exc:
        raise RuntimeError("The LLM returned a response that could not be validated.") from exc
