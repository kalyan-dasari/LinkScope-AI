# LinkScope AI &mdash; Intelligent Website Link Analysis API

LinkScope AI is an assessment-grade, AI-powered website analysis microservice built with **FastAPI**, **HTTPX**, **BeautifulSoup**, and **Google Gemini 2.0 Flash**.

It crawls any public website, extracts clean semantic content, guards against Server-Side Request Forgery (SSRF), and produces validated, structured intelligence covering:
1. **Competitor Analysis** (market positioning, differentiators, opportunities, and verification status)
2. **High-Intent Search Queries** (strictly 5 cross-platform search queries across Google, LinkedIn, X, etc.)
3. **Actionable SEO Recommendations** (primary, secondary, and long-tail keywords, title tag, and meta description)
4. **Top Services & Products** (target verticals, customer personas, primary benefits)
5. **Target Audience Segmentation** (demographics, industries, business types, pain points, and personas)

---

## Architecture Overview

```
                      +-----------------------------+
                      | Client (HTTP /docs / curl)   |
                      +--------------+--------------+
                                     |
                                     v
                 +---------------------------------------+
                 |  FastAPI Router (POST /link-analysis) |
                 +-------------------+-------------------+
                                     |
                                     v
                 +---------------------------------------+
                 | Analysis Service (Orchestrator)       |
                 +----------+-----------------+----------+
                            |                 |
            Content Crawl   |                 | Structured LLM
                            v                 v
          +-----------------------+     +--------------------------+
          | Website Extractor     |     | LLM Service              |
          | - HTTPX AsyncClient   |     | - Google GenAI SDK       |
          | - BeautifulSoup DOM   |     | - Gemini 2.0 Flash       |
          | - Multi-hop Redirects |     | - Native JSON Schema     |
          | - 2MB Body Streaming  |     | - asyncio.to_thread Offload|
          +-----------+-----------+     +--------------------------+
                      |
                      v
          +-----------------------+
          | SSRF Validator        |
          | - Scheme verification |
          | - IP / Link-Local drop|
          | - Metadata / DNS check|
          +-----------------------+
```

---

## Features

- **Asynchronous Scraping**: Concurrent page fetching via `httpx.AsyncClient` with `asyncio.gather`.
- **SSRF Defense-in-Depth**:
  - Enforces `http` / `https` protocols.
  - Rejects `localhost`, `.local`, `.internal`, and user credentials in URLs.
  - Rejects non-global, loopback, private, link-local, and cloud metadata IPs (`169.254.169.254`).
  - Re-evaluates URLs across every redirect hop (up to 5 hops).
  - Streams response bodies with a 2MB cap to prevent memory exhaustion / zip bombs.
- **Strict Pydantic v2 Output**: Output adheres to `AnalysisPayload` schemas enforced via Gemini's native JSON Schema mode.
- **Granular HTTP Status Codes**:
  - `200 OK`: Successful structured report.
  - `400 Bad Request`: Malformed URL, unsupported protocol, or SSRF violation.
  - `422 Unprocessable Entity`: Thin or empty website content (< 100 characters).
  - `502 Bad Gateway`: Target website unreachable, timed out, or LLM service failure.
  - `503 Service Unavailable`: Missing or misconfigured `GEMINI_API_KEY`.
  - `500 Internal Server Error`: Unexpected internal exceptions (sanitized from client).
- **CORS Enabled**: Configured for cross-origin access by frontends or API gateways.
- **Container Ready**: Includes production multi-stage `Dockerfile` and `docker-compose.yml`.

---

## Project Structure

```text
app/
  main.py                 # FastAPI application, CORS middleware, root & health routes
  config.py               # Pydantic Settings configuration from .env
  exceptions.py           # Domain exception taxonomy (InvalidUrlError, etc.)
  schemas.py              # Pydantic v2 schemas for requests, responses, and LLM payloads
  prompts/
    analysis_prompt.py    # Structured analysis prompt & system instructions
  routes/
    analysis.py           # POST /link-analysis endpoint with OpenAPI error schemas
  services/
    analysis_service.py   # Business logic coordinator & async thread offloading
    website_extractor.py  # Safe HTTPX crawler with DOM extraction & redirect validation
    llm_service.py        # Gemini client integration & schema-validated inference
  utils/
    url_validator.py      # SSRF, DNS resolution, and cloud metadata filtering
tests/
  test_url_validator.py   # SSRF & URL validation test suite
  test_extractor.py       # DOM extraction, HTML pruning, and page selection tests
  test_schemas.py         # Pydantic schema validation & constraint tests
  test_mock_analysis.py   # Unit tests with mocked Gemini client & API key checks
Dockerfile                # Production container specification
docker-compose.yml        # Multi-container orchestration
requirements.txt          # Python dependencies
```

---

## Quickstart

### 1. Local Setup

```powershell
# 1. Create and activate a virtual environment
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
Copy-Item .env.example .env
# Edit .env and supply your GEMINI_API_KEY (from Google AI Studio)

# 4. Run automated test suite
python -m pytest

# 5. Start the development server
uvicorn app.main:app --reload --port 8000
```

Open:
- **Interactive OpenAPI Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check Probe**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

### 2. Docker Deployment

```bash
# Build and run container
docker build -t linkscope-ai .
docker run -p 8000:8000 --env GEMINI_API_KEY="your_api_key_here" linkscope-ai

# Or with docker-compose
docker compose up --build
```

---

## API Usage

### Endpoint: `POST /link-analysis`

**Request Headers:** `Content-Type: application/json`

**Request Body:**
```json
{
  "url": "https://example.com"
}
```

**cURL:**
```bash
curl -X POST "http://127.0.0.1:8000/link-analysis" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com"}'
```

**PowerShell:**
```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/link-analysis" `
  -ContentType "application/json" `
  -Body '{"url":"https://example.com"}'
```

**Sample Response:**
```json
{
  "success": true,
  "website": "https://example.com",
  "brand": {
    "name": "Example Domain",
    "category": "Documentation & Standards",
    "summary": "Illustrative domain managed by IANA for documentation and examples.",
    "source": "website_content"
  },
  "analysis": {
    "competitor_analysis": {
      "brand_overview": "Standard domain used for documentation...",
      "competitors": [
        {
          "name": "IETF RFC Standards",
          "website": "https://ietf.org",
          "strengths": ["Global RFC authority", "Industry trust"],
          "weaknesses_or_gaps": ["Technical syntax focus"],
          "verification_status": "ai_suggested",
          "notes": "Direct peer in reference standards"
        }
      ],
      "brand_strengths": ["Globally recognized", "Zero maintenance overhead"],
      "competitive_advantages": ["Standardized by IETF"],
      "opportunities": ["Broader interactive documentation"]
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
      "recommended_title": "Example Domain &mdash; Official Illustrative Reference",
      "meta_description": "Official documentation domain established by IANA for illustrative use in documents and test environments without prior coordination.",
      "supporting_content": ["Guide to RFC Reserved Domains", "Best Practices for Mock URLs in APIs"]
    },
    "top_services": [
      {
        "name": "Documentation Reference",
        "description": "Provides a safe, universally recognized URL for technical writing.",
        "target_industry": ["Software", "Education", "Publishing"],
        "target_customer": ["Technical Writers", "Engineers"],
        "main_benefit": "Eliminates risk of linking to active commercial or hostile sites.",
        "source": "website"
      }
    ],
    "target_audience": {
      "primary_audience": ["Software Developers", "Technical Writers"],
      "secondary_audience": ["Network Administrators", "Educators"],
      "industries": ["Information Technology", "Higher Education"],
      "business_types": ["B2B", "Open Source", "Standards Bodies"],
      "customer_profiles": ["Technical Authors", "API Architects"],
      "geographical_focus": ["Global"],
      "customer_needs": ["Reliable, non-colliding example domains for documentation"],
      "interests": ["Networking", "RFC Standards", "API Design"],
      "marketing_segments": ["Developer Tooling", "Technical Education"]
    }
  },
  "metadata": {
    "pages_analyzed": 1,
    "analysis_model": "gemini-2.0-flash",
    "processing_time_seconds": 2.45
  }
}
```

---

## Interview Defense & Technical Decisions

### 1. Why FastAPI?
- **Asynchronous Concurrency**: Crawling websites and invoking LLMs are I/O-bound tasks. FastAPI runs on top of Starlette and `uvicorn`, enabling high throughput on a single thread without blocking while waiting for external network I/O.
- **Pydantic v2 Schema Validation**: Validates both incoming requests and outgoing payloads with native C-speed (`pydantic-core`), generating interactive OpenAPI/Swagger docs automatically.

### 2. Why HTTPX + BeautifulSoup over Playwright / Selenium?
- **Resource Footprint**: Headless browsers require ~300MB RAM per worker instance and significant CPU overhead. HTTPX with connection pooling and BeautifulSoup parses HTML in a fraction of the time and uses only a few megabytes.
- **Trade-Off**: For SPAs (Single Page Applications) relying heavily on client-side JS rendering, a headless browser is required. LinkScope AI optimizes for speed, security, and low cost for the 95% of content-rich websites, and raises a descriptive `422 Unprocessable Entity` when insufficient HTML text is found.

### 3. How does LinkScope AI defend against SSRF and DNS Rebinding?
- **Scheme & Port Whitelisting**: Only `http`/`https` protocols and standard web ports (80, 443, 8080, 8443) are accepted.
- **IP Validation**: Literal IPs and resolved DNS records are parsed via Python's `ipaddress` module to reject loopback (`127.0.0.0/8`), private (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), link-local, and cloud metadata addresses (`169.254.169.254`).
- **Redirect Chain Validation**: HTTP redirects are not followed automatically; instead, each hop is intercepted and re-validated through `validate_public_url()` up to a 5-hop limit.
- **Memory Bounding**: Streams HTML bodies with a 2MB cap to prevent memory exhaustion / decompression bomb attacks.
- *Interview Note on TOCTOU*: In application-level validation, there is a small window between DNS resolution in `validate_public_url()` and the subsequent socket connection made by `httpx.AsyncClient`. In high-security production deployments, this is supplemented by network egress firewalls or custom transport hooks that bind directly to the validated IP.

### 4. Why `asyncio.to_thread` for the Gemini API call?
- The Google GenAI SDK `generate_content` method performs blocking network I/O. Calling a blocking function directly inside an `async def` route would freeze the entire asyncio event loop, blocking all other concurrent requests. Wrapping it in `asyncio.to_thread` delegates the blocking call to a worker thread pool while keeping the event loop responsive.

---

## License

MIT License. Designed for assessment and enterprise evaluation.
