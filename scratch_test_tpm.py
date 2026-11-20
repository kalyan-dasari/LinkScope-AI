import time
import json
from groq import Groq
from app.config import settings
from app.schemas import AnalysisPayload
from app.prompts.analysis_prompt import build_analysis_prompt

client = Groq(api_key=settings.groq_api_key)

test_context = {
    'website': 'https://www.studearning.tech/',
    'pages_analyzed_count': 1,
    'pages': [
        {
            'url': 'https://www.studearning.tech/',
            'title': 'StudEarn — Student Services Marketplace',
            'meta_description': 'StudEarn is a student services marketplace where students request services, collaborate on tasks, share resources, and connect directly with fellow student service providers.',
            'headings': [],
            'content': 'Title: StudEarn — Student Services Marketplace\nMeta Description: StudEarn is a student services marketplace where students request services, collaborate on tasks, share resources, and connect directly with fellow student service providers.'
        }
    ]
}

prompt = build_analysis_prompt(test_context)
compact_schema = json.dumps(AnalysisPayload.model_json_schema())

system_msg = (
    f"{prompt}\n\n"
    f"CONCISENESS REQUIREMENT: Be concise and factual. Keep bullet points, summaries, and descriptions to 1-2 punchy sentences. "
    f"Do NOT write long paragraphs. Complete all 5 sections within 1,500 tokens.\n\n"
    f"You MUST return a JSON object with top-level keys 'brand' and 'analysis'.\n"
    f"'analysis' MUST contain all 5 sections:\n"
    f"1. 'competitor_analysis'\n"
    f"2. 'target_search_queries' (EXACTLY 5 items)\n"
    f"3. 'seo_improvements'\n"
    f"4. 'top_services' (between 1 and 5 items)\n"
    f"5. 'target_audience'\n"
    f"Schema: {compact_schema}"
)

t0 = time.perf_counter()
try:
    completion = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": "Produce the complete validated JSON report for StudEarn."},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=3000,
    )
    elapsed = round(time.perf_counter() - t0, 2)
    print(f"SUCCESS in {elapsed}s!")
    print(f"Usage: {completion.usage.total_tokens} tokens (completion: {completion.usage.completion_tokens}, prompt: {completion.usage.prompt_tokens})")
    raw = completion.choices[0].message.content
    validated = AnalysisPayload.model_validate_json(raw)
    print("VALIDATION PASSED!")
    print("Brand:", validated.brand.name)
    print("Competitors:", [c.name for c in validated.analysis.competitor_analysis.competitors])
    print("Queries:", len(validated.analysis.target_search_queries))
    print("Services:", [s.name for s in validated.analysis.top_services])
    print("Target Audience:", validated.analysis.target_audience.primary_audience)
except Exception as e:
    print("FAILED ->", e)
