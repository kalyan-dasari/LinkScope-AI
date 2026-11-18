# LinkScope AI — Website Link Analysis API

Python/FastAPI practical assessment starter implementation.

## Features
- `POST /link-analysis`: analyzes a website URL and returns five structured insight sections.
- `GET /health`: service health check.
- Website fetching and extraction with HTTPX + BeautifulSoup.
- Single-call structured LLM analysis through Gemini API (configurable via env).
- Pydantic response validation.
- URL validation and basic SSRF protections (blocks localhost/private IPs, checks DNS resolutions).
- Limited internal-page discovery (homepage + up to 4 relevant pages).
- Graceful handling of invalid URLs, fetch failures, and model errors.

> Competitor analysis and search queries are AI-generated suggestions unless external search data is integrated. No search volume/ranking metrics are fabricated.

## Requirements
- Python 3.11+
- Gemini API key (get one via Google AI Studio). API key is only used by this Python backend; do not commit it.

## Setup (Windows / PowerShell)
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# edit .env and add GEMINI_API_KEY
uvicorn app.main:app --reload --port 4000
```

Open:
- API docs: http://127.0.0.1:4000/docs
- Health: http://127.0.0.1:4000/health

## Test the endpoint
In Swagger (`/docs`), select `POST /link-analysis` and use:
```json
{
  "url": "https://example.com"
}
```
Or PowerShell:
```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:4000/link-analysis" -ContentType "application/json" -Body '{"url":"https://example.com"}'
```

## Environment variables
See `.env.example`.

## Project structure
```text
app/
  main.py
  config.py
  schemas.py
  routes/analysis.py
  services/website_extractor.py
  services/llm_service.py
  services/analysis_service.py
  prompts/analysis_prompt.py
  utils/url_validator.py
tests/
  test_url_validator.py
```

## Notes / limitations
- This is an initial working version, not a claim of production-grade crawler security.
- SSRF protection is best-effort in this implementation. For deployment, use network-level egress restrictions and revalidate every redirect.
- Many JavaScript-rendered websites may expose little content to the HTML parser.
- A website may block automated requests or require authentication.
- Competitor verification requires a search provider; currently competitor suggestions are labeled `ai_suggested`.
- Model costs and response times need to be measured for your own test set and documented in the assessment.

## Suggested next steps
1. Run locally and test 3–5 different sites.
2. Review and improve extraction quality.
3. Tune the analysis prompt.
4. Add provider/model comparison to README based on current official pricing and measured latency.
5. Add tests for extractor and LLM parsing.
6. Deploy and verify live URL.
