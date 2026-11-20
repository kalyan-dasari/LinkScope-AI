import time
from groq import Groq
from app.config import settings
from app.schemas import AnalysisPayload

client = Groq(api_key=settings.groq_api_key)

schema_skeleton = """{
  "brand": {
    "name": "string",
    "category": "string",
    "summary": "string",
    "source": "website_content"
  },
  "analysis": {
    "competitor_analysis": {
      "brand_overview": "string",
      "business_model": "string",
      "main_products_or_services": ["string"],
      "competitors": [
        {
          "name": "Competitor 1",
          "website": "https://example.com",
          "description": "string",
          "strengths": ["string"],
          "weaknesses": ["string"],
          "verification_status": "ai_suggested",
          "notes": "string"
        },
        {
          "name": "Competitor 2",
          "website": "https://example.com",
          "description": "string",
          "strengths": ["string"],
          "weaknesses": ["string"],
          "verification_status": "ai_suggested",
          "notes": "string"
        },
        {
          "name": "Competitor 3",
          "website": "https://example.com",
          "description": "string",
          "strengths": ["string"],
          "weaknesses": ["string"],
          "verification_status": "ai_suggested",
          "notes": "string"
        }
      ],
      "brand_strengths": ["string"],
      "brand_weaknesses": ["string"],
      "competitive_gaps": ["string"],
      "competitive_advantages": ["string"],
      "opportunities": ["string"]
    },
    "target_search_queries": [
      {"query": "string", "platforms": ["Google"], "intent": "Commercial", "business_relevance": "string", "target_audience": "string"},
      {"query": "string", "platforms": ["Google"], "intent": "Informational", "business_relevance": "string", "target_audience": "string"},
      {"query": "string", "platforms": ["Google"], "intent": "Transactional", "business_relevance": "string", "target_audience": "string"},
      {"query": "string", "platforms": ["LinkedIn"], "intent": "Commercial", "business_relevance": "string", "target_audience": "string"},
      {"query": "string", "platforms": ["Google"], "intent": "Navigational", "business_relevance": "string", "target_audience": "string"}
    ],
    "seo_improvements": {
      "primary_keyword": "string",
      "secondary_keywords": ["string"],
      "long_tail_keywords": ["string"],
      "business_related_keywords": ["string"],
      "recommended_title": "string",
      "meta_description": "string",
      "content_recommendations": ["string"],
      "on_page_improvements": ["string"],
      "technical_seo_suggestions": ["string"]
    },
    "top_services": [
      {
        "name": "string",
        "description": "string",
        "target_industry": ["string"],
        "target_customer": ["string"],
        "main_benefit": "string",
        "source": "extracted"
      }
    ],
    "target_audience": {
      "primary_audience": ["string"],
      "secondary_audience": ["string"],
      "industry_segments": ["string"],
      "business_types": ["string"],
      "customer_profiles": ["string"],
      "geographic_markets": ["string"],
      "customer_needs": ["string"],
      "customer_interests": ["string"],
      "marketing_segments": ["string"],
      "targeting_opportunities": ["string"],
      "source_classification": "inferred"
    }
  }
}"""

prompt = f"""You are a website business analyst. Analyze this website evidence and produce the complete JSON report.

WEBSITE EVIDENCE:
Title: StudEarn — Student Services Marketplace
Meta Description: StudEarn is a student services marketplace where students request services, collaborate on tasks, share resources, and connect directly with fellow student service providers.

CRITICAL INSTRUCTIONS:
- competitor_analysis.competitors MUST contain at least 3 relevant competitors (direct or indirect).
- target_search_queries MUST contain EXACTLY 5 search query objects.
- top_services MUST contain between 1 and 5 service objects.
- Keep each description and summary concise (1-2 sentences).
- Output MUST be valid JSON adhering strictly to this structure:
{schema_skeleton}
"""

t0 = time.perf_counter()
res = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": prompt}],
    response_format={"type": "json_object"},
    temperature=0.2,
    max_tokens=3500,
)
elapsed = round(time.perf_counter() - t0, 2)
print(f"SUCCESS in {elapsed}s! Tokens: {res.usage.total_tokens} (prompt: {res.usage.prompt_tokens}, completion: {res.usage.completion_tokens})")
validated = AnalysisPayload.model_validate_json(res.choices[0].message.content)
print("Brand:", validated.brand.name)
print("Competitors count:", len(validated.analysis.competitor_analysis.competitors), [c.name for c in validated.analysis.competitor_analysis.competitors])
print("Queries count:", len(validated.analysis.target_search_queries))
print("Services count:", len(validated.analysis.top_services), [s.name for s in validated.analysis.top_services])
print("Audience needs:", validated.analysis.target_audience.customer_needs)
