# LinkScope AI &mdash; Intelligent Website Link Analysis API

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2.8+-e92063.svg)](https://docs.pydantic.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Chivox AI Python Practical Assessment Submission**  
Production-ready, AI-powered link analysis microservice that crawls public websites, guards against SSRF attacks, and extracts deep competitive intelligence, high-intent search queries, actionable SEO audits, service catalogs, and audience personas via Google Gemini 2.0 Flash.

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Features](#2-features)
3. [Tech Stack](#3-tech-stack)
4. [Architecture](#4-architecture)
5. [Project Structure](#5-project-structure)
6. [Installation Instructions](#6-installation-instructions)
7. [Environment Configuration](#7-environment-configuration)
8. [How to Run Locally](#8-how-to-run-locally)
9. [API Endpoints](#9-api-endpoints)
10. [Sample Request](#10-sample-request)
11. [Sample Response](#11-sample-response)
12. [Error Response Examples](#12-error-response-examples)
13. [How to Configure the LLM](#13-how-to-configure-the-llm)
14. [Testing Instructions](#14-testing-instructions)
15. [Deployment Instructions](#15-deployment-instructions)
16. [Security Considerations](#16-security-considerations)
17. [Known Limitations](#17-known-limitations)

---

## 1. Project Overview

LinkScope AI accepts any public website URL via `POST /link-analysis`, discovers and crawls the homepage plus up to 4 key semantic internal pages (`/about`, `/services`, etc.), strips boilerplate HTML with BeautifulSoup, and performs structured semantic analysis using the Google GenAI SDK.

The returned JSON adheres to strict Pydantic models covering:
- **Competitor vs Brand Analysis**: Market positioning, business models, at least 3 direct/indirect competitors (labeled as `verified` or `ai_suggested`), brand strengths, brand weaknesses, competitive gaps, USPs, and opportunities.
- **Top 5 Target Search Queries**: High-intent queries mapped to specific platforms (Google, LinkedIn, X, YouTube), search intent, target audience personas, and business acquisition relevance.
- **SEO Recommendations**: Primary, secondary, and long-tail keywords, suggested title tag (50-60 chars) and meta description (140-160 chars), topic cluster recommendations, on-page fixes, and technical SEO guidance.
- **Top 5 Services**: Core products/services, target industries, buyer personas, ROI benefits, and explicit source classification (`extracted` vs `inferred`).
- **Target Audience Segmentation**: Primary and secondary audiences, vertical industries, business models, customer profiles, geographic markets, pain points, and targeting opportunities.

---

## 2. Features

- **Non-Blocking Async Crawler**: Multi-page concurrent fetching using `httpx.AsyncClient` with pooled connections and `asyncio.gather`.
- **SSRF Defense-in-Depth**:
  - Whitelists only `http` and `https` schemes.
  - Drops requests targeting non-standard administrative ports (allows 80, 443, 8080, 8443).
  - Blocks `localhost`, `.local`, `.internal`, and user credentials in URLs.
  - Resolves hostnames against DNS and verifies all IP addresses are globally routable (rejects loopback, private RFC 1918, link-local, and cloud metadata `169.254.169.254`).
  - Intercepts and re-validates *every single HTTP redirect hop* (up to 5 hops) to prevent redirect-based SSRF.
  - Streams responses with a 2MB cap per page to prevent memory bombs and DoS.
- **Strict Pydantic v2 Output**: Output is governed by schema validation enforced natively by Gemini 2.0 Flash (`response_schema=AnalysisPayload`).
- **Granular Status Code Taxonomy**: Maps domain exceptions cleanly to RFC-compliant HTTP status codes (`400`, `422`, `502`, `503`, `500`).
- **Modular Provider Architecture**: Features an abstract `BaseLLMProvider` interface permitting seamless swaps between Gemini, OpenAI, or Claude.
- **CORS Configured**: Cross-Origin Resource Sharing enabled for browser clients, web extensions, or Swagger UI.

---

## 3. Tech Stack

- **Framework**: [FastAPI 0.115+](https://fastapi.tiangolo.com/) (ASGI, Python 3.11+)
- **Server**: [Uvicorn](https://www.uvicorn.org/) (High-performance ASGI server)
- **HTTP Client**: [HTTPX](https://www.python-httpx.org/) (Async HTTP/1.1 and HTTP/2 client)
- **HTML Parsing**: [BeautifulSoup 4](https://beautiful-soup-4.readthedocs.io/) (DOM parsing & semantic text extraction)
- **Data Validation & Settings**: [Pydantic v2](https://docs.pydantic.dev/) & [pydantic-settings](https://github.com/pydantic/pydantic-settings)
- **AI / LLM Engine**: [Google GenAI SDK](https://github.com/googleapis/python-genai) (`gemini-2.0-flash`)
- **Testing**: [Pytest](https://docs.pytest.org/) & [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- **Containerization**: [Docker](https://www.docker.com/) & Docker Compose

---

## 4. Architecture

```
                 +-----------------------------------+
                 | Client (HTTP / Swagger / cURL)    |
                 +-----------------+-----------------+
                                   |
                                   v
             +-------------------------------------------+
             | FastAPI Application Router                |
             | - POST /link-analysis                     |
             | - GET /health                             |
             | - GET /                                   |
             +---------------------+---------------------+
                                   |
                                   v
             +-------------------------------------------+
             | Analysis Service Coordinator              |
             +-----------+-------------------+-----------+
                         |                   |
         Content Crawl   |                   | Structured LLM
                         v                   v
       +-----------------------+     +-------------------------------+
       | Website Extractor     |     | LLM Service (Provider Pattern)|
       | - HTTPX AsyncClient   |     | - BaseLLMProvider             |
       | - BeautifulSoup DOM   |     | - GeminiProvider (2.0 Flash)  |
       | - Multi-hop Redirects |     | - Native JSON Schema Enforced |
       | - 2MB Stream Bounding |     | - asyncio.to_thread Offloading|
       +-----------+-----------+     +-------------------------------+
                   |
                   v
       +-----------------------+
       | SSRF / URL Validator  |
       | - Protocol Whitelist  |
       | - IP & Link-Local Drop|
       | - Metadata Filtering  |
       +-----------------------+
```

For comprehensive deep-dive sequence diagrams and design choices, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 5. Project Structure

```text
app/
  __init__.py
  main.py                 # FastAPI application, CORS middleware, root & health routes
  config.py               # Pydantic Settings configuration from .env
  exceptions.py           # Domain exception hierarchy (InvalidUrlError, etc.)
  schemas.py              # Pydantic v2 schemas for requests, responses, and LLM payloads
  prompts/
    __init__.py
    analysis_prompt.py    # Structured analysis prompt & system instructions
  routes/
    __init__.py
    analysis.py           # POST /link-analysis route handler with OpenAPI responses
  services/
    __init__.py
    analysis_service.py   # Business logic coordinator & async thread offloading
    website_extractor.py  # Safe HTTPX crawler with DOM pruning & redirect validation
    llm_service.py        # Modular LLM provider architecture (GeminiProvider)
  utils/
    __init__.py
    url_validator.py      # SSRF defense, DNS resolution, and cloud metadata filtering
docs/
  ARCHITECTURE.md         # Full system architecture, sequence diagrams, and design rationales
  LLM_MODEL_COMPARISON.md # Benchmark comparing Gemini 2.0 Flash, OpenAI, and Claude
  API_EXAMPLES.md         # Detailed illustrative request/response payloads
tests/
  test_url_validator.py   # SSRF, DNS, and IP boundary test suite
  test_extractor.py       # DOM extraction, HTML pruning, and page selection tests
  test_schemas.py         # Pydantic schema validation & constraint tests
  test_mock_analysis.py   # Unit tests with mocked Gemini client & API key checks
  test_api.py             # End-to-end route tests (health, root, error cases, SSRF)
Dockerfile                # Production multi-stage container
docker-compose.yml        # Docker Compose orchestration
Procfile                  # PaaS process file (Render, Railway, Heroku)
pytest.ini                # Pytest configuration
requirements.txt          # Production and test dependencies
.env.example              # Environment variables template
```

---

## 6. Installation Instructions

### Prerequisites
- Python 3.11, 3.12, 3.13, or 3.14
- Git

### Setup
```powershell
# Clone repository
git clone https://github.com/kalyan-dasari/LinkScope-AI.git
cd LinkScope-AI

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 7. Environment Configuration

Copy `.env.example` to create `.env`:
```powershell
Copy-Item .env.example .env
```

Edit `.env` and supply your Gemini API key (obtainable freely from [Google AI Studio](https://aistudio.google.com/)):

```ini
# LLM Configuration
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# Crawler and Security Limits
REQUEST_TIMEOUT_SECONDS=15
MAX_PAGES=5
MAX_CONTENT_CHARS=24000
MAX_RESPONSE_BYTES=2097152
MAX_REDIRECTS=5
```

---

## 8. How to Run Locally

Start the development server with Uvicorn:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access the service:
- **Interactive OpenAPI Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Alternative Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Service Health Probe**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 9. API Endpoints

| Method | Endpoint | Description | Response Codes |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | API metadata, version, and documentation links | `200 OK` |
| `GET` | `/health` | Liveness and readiness health probe | `200 OK` |
| `POST` | `/link-analysis` | Crawls website and performs AI analysis | `200`, `400`, `422`, `502`, `503`, `500` |

---

## 10. Sample Request

### cURL:
```bash
curl -X POST "http://127.0.0.1:8000/link-analysis" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com"}'
```

### PowerShell:
```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/link-analysis" `
  -ContentType "application/json" `
  -Body '{"url": "https://example.com"}'
```

---

## 11. Sample Response

*(Illustrative Example for Testing)*

```json
{
  "success": true,
  "website": "https://example.com/",
  "brand": {
    "name": "Example Domain",
    "category": "Documentation & Standards",
    "summary": "Illustrative domain managed by IANA for documentation and testing without prior coordination.",
    "source": "website_content"
  },
  "analysis": {
    "competitor_analysis": {
      "brand_overview": "Standard domain used across RFC documentation.",
      "business_model": "Non-profit internet standards governance.",
      "main_products_or_services": [
        "Documentation illustrative domain",
        "Sample URL testing standard"
      ],
      "competitors": [
        {
          "name": "IETF RFC Standards",
          "website": "https://ietf.org",
          "description": "Internet standards and specifications body.",
          "strengths": ["Global RFC authority", "Industry trust"],
          "weaknesses": ["Technical syntax focus"],
          "verification_status": "ai_suggested",
          "notes": "Direct peer in reference standards"
        }
      ],
      "brand_strengths": ["Globally recognized", "Zero maintenance overhead"],
      "brand_weaknesses": ["Contains no interactive content or documentation search"],
      "competitive_gaps": ["Third-party mock API sites provide dynamic payload endpoints"],
      "competitive_advantages": ["Reserved by IANA under RFC 2606 and RFC 6761"],
      "opportunities": ["Broader interactive documentation guides"]
    },
    "target_search_queries": [
      {
        "query": "documentation test domain example",
        "platforms": ["Google", "GitHub"],
        "intent": "Informational",
        "business_relevance": "Developers needing sample URLs in technical tutorials",
        "target_audience": "Software Developers"
      },
      {
        "query": "rfc 2606 reserved domains",
        "platforms": ["Google"],
        "intent": "Informational",
        "business_relevance": "Network engineers verifying reserved names",
        "target_audience": "Network Architects"
      },
      {
        "query": "how to test mock links in api",
        "platforms": ["Google", "StackOverflow"],
        "intent": "Commercial",
        "business_relevance": "QA engineers configuring integration tests",
        "target_audience": "QA Engineers"
      },
      {
        "query": "iana reserved domain names list",
        "platforms": ["Google"],
        "intent": "Navigational",
        "business_relevance": "Legal and compliance specialists auditing domains",
        "target_audience": "Compliance Officers"
      },
      {
        "query": "mock website url for frontend testing",
        "platforms": ["Google", "Reddit"],
        "intent": "Transactional",
        "business_relevance": "Frontend teams building link preview components",
        "target_audience": "Frontend Developers"
      }
    ],
    "seo_improvements": {
      "primary_keyword": "example domain",
      "secondary_keywords": ["iana documentation", "test domain", "reserved domain"],
      "long_tail_keywords": ["how to use example.com in documentation", "rfc 2606 reserved domains list"],
      "business_related_keywords": ["rfc standards", "mock url"],
      "recommended_title": "Example Domain &mdash; Official Illustrative Reference",
      "meta_description": "Official documentation domain established by IANA for illustrative use in documents and test environments without prior coordination.",
      "content_recommendations": ["Guide to RFC Reserved Domains", "Best Practices for Mock URLs in APIs"],
      "on_page_improvements": ["Add clear links to RFC 2606 specifications"],
      "technical_seo_suggestions": ["Ensure canonical link tag is present in HTML head"]
    },
    "top_services": [
      {
        "name": "Documentation Reference",
        "description": "Provides a safe, universally recognized URL for technical writing.",
        "target_industry": ["Software", "Education", "Publishing"],
        "target_customer": ["Technical Writers", "Engineers"],
        "main_benefit": "Eliminates risk of linking to active commercial or hostile sites.",
        "source": "extracted"
      }
    ],
    "target_audience": {
      "primary_audience": ["Software Developers", "Technical Writers"],
      "secondary_audience": ["Network Administrators", "Educators"],
      "industry_segments": ["Information Technology", "Higher Education"],
      "business_types": ["B2B", "Open Source", "Standards Bodies"],
      "customer_profiles": ["Technical Authors", "API Architects"],
      "geographic_markets": ["Global"],
      "customer_needs": ["Reliable, non-colliding example domains for documentation"],
      "customer_interests": ["Networking", "RFC Standards", "API Design"],
      "marketing_segments": ["Developer Tooling", "Technical Education"],
      "targeting_opportunities": ["Developer documentation portals and university CS curricula"],
      "source_classification": "website_confirmed"
    }
  },
  "metadata": {
    "pages_analyzed": 1,
    "analysis_model": "gemini-2.0-flash",
    "processing_time_seconds": 1.85
  }
}
```

---

## 12. Error Response Examples

### A. SSRF / Private IP Target (HTTP 400 Bad Request)
```json
{
  "detail": "Private, loopback, link-local, or cloud metadata IP addresses are not allowed."
}
```

### B. Thin or Empty Website Content (HTTP 422 Unprocessable Content)
```json
{
  "detail": "The website at 'https://example.com' did not provide sufficient readable text (18 characters extracted). It may be heavily JavaScript-dependent, password-protected, or empty."
}
```

### C. Unreachable Website / Timeout (HTTP 502 Bad Gateway)
```json
{
  "detail": "Connection to 'https://slow-site.com' timed out after 15.0s."
}
```

### D. Missing Gemini API Key (HTTP 503 Service Unavailable)
```json
{
  "detail": "GEMINI_API_KEY is not configured. Please supply a valid Gemini API key in your .env file."
}
```

---

## 13. How to Configure the LLM

LinkScope AI uses Google's `gemini-2.0-flash` by default.

To configure or tune:
1. In `.env`, ensure `GEMINI_API_KEY` is set to your Google AI Studio API key.
2. Change model variant if desired:
   ```ini
   GEMINI_MODEL=gemini-2.0-flash
   # or GEMINI_MODEL=gemini-1.5-pro
   ```
3. To learn about alternative providers (OpenAI GPT-4o, Anthropic Claude 3.5), review [docs/LLM_MODEL_COMPARISON.md](docs/LLM_MODEL_COMPARISON.md).

---

## 14. Testing Instructions

The automated test suite runs **100% offline with zero paid API calls** by mocking network extraction and Gemini LLM calls.

```powershell
# Run the complete test suite
pytest

# Run with verbose output and coverage
pytest -v
```

### Test Suite Modules
- `tests/test_url_validator.py`: Tests scheme validation, localhost, private RFC 1918 IPs, link-local metadata (169.254.169.254), dangerous ports, and DNS resolution.
- `tests/test_extractor.py`: Tests BeautifulSoup tag decomposition, metadata extraction, semantic text extraction, and relevant internal link scoring.
- `tests/test_schemas.py`: Tests strict Pydantic v2 validation (e.g. enforcing exactly 5 search queries).
- `tests/test_mock_analysis.py`: Tests `analyze_content` with mocked Google GenAI client and missing API key exceptions.
- `tests/test_api.py`: Tests `/health`, `/`, SSRF rejection, thin content handling, 404/502 handling, and full end-to-end mocked link analysis.

---

## 15. Deployment Instructions

### Docker (Recommended)
```bash
# Build the container
docker build -t linkscope-ai .

# Run the container
docker run -d -p 8000:8000 \
  --name linkscope \
  -e GEMINI_API_KEY="your_api_key_here" \
  linkscope-ai
```

### Cloud Run / Render / Railway
1. **Repository**: Link your GitHub repository.
2. **Buildpack**: Select Dockerfile (or Python buildpack).
3. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (Provided via `Procfile`).
4. **Environment Variables**: Add `GEMINI_API_KEY` in your provider dashboard.
5. **Health Check Path**: `/health`.

---

## 16. Security Considerations

1. **SSRF Defense**: The API acts as an outbound web crawler, making SSRF protection paramount. Every URL and every redirect hop is validated against RFC 1918 private subnets, loopback interfaces (`127.0.0.0/8`, `::1`), link-local subnets (`169.254.0.0/16`), and dangerous internal ports.
2. **Time-Of-Check to Time-Of-Use (TOCTOU) & DNS Rebinding**:
   - `validate_public_url` resolves DNS and verifies IP safety before connection.
   - For high-security environments, pair this with network egress filtering or IP-bound transport hooks.
3. **Decompression & Memory Bombs**:
   - Responses are read in streaming chunks up to a 2MB maximum limit (`settings.max_response_bytes`). Excess bytes trigger immediate connection termination.
4. **Information Leakage**:
   - Internal stack traces, raw database errors, and API keys are strictly masked from client HTTP responses.

---

## 17. Known Limitations

1. **Client-Side Rendered Applications (SPAs)**:
   - Websites that render 100% of text dynamically via JavaScript (e.g., blank React/Vue roots) expose little HTML text to standard HTTPX scrapers. LinkScope AI detects this and returns a descriptive `422 Unprocessable Content` rather than returning degraded AI hallucinations. Headless browsers (e.g. Playwright) can be plugged in for heavy SPA rendering at the cost of higher RAM usage.
2. **Aggressive Anti-Bot Cloudflare Captchas**:
   - Sites protected by Cloudflare Turnstile or aggressive bot mitigations may return `403 Forbidden`. The service catches this and provides a clear error message.
3. **Competitor Data Verification**:
   - Competitors suggested by the AI are marked `ai_suggested` unless explicitly corroborated in website text. Live verified search ranking metrics require integration with paid search data providers (e.g., Semrush or Ahrefs).

---

## License

MIT License. Designed and verified for the Chivox AI Practical Assessment.
