# LinkScope AI &mdash; API Reference & Illustrative Examples

> [!NOTE]
> **Assessment Disclaimer**: The JSON payloads below are illustrative reference examples demonstrating the exact schema and data granularity emitted by LinkScope AI. They are provided for testing, documentation, and evaluation purposes.

---

## 1. General Endpoints

### `GET /`
Returns API metadata, version, and links to interactive Swagger documentation.

**Request:**
```bash
curl -X GET "http://127.0.0.1:8000/"
```

**Response (200 OK):**
```json
{
  "name": "LinkScope AI",
  "description": "AI-powered website, competitor, SEO, and audience analysis API",
  "version": "1.0.0",
  "documentation": "/docs",
  "health_check": "/health",
  "analysis_endpoint": "POST /link-analysis"
}
```

---

### `GET /health`
Kubernetes and container orchestrator liveness/readiness probe.

**Request:**
```bash
curl -X GET "http://127.0.0.1:8000/health"
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "service": "LinkScope AI"
}
```

---

### `GET /demo`
Visual interactive dashboard for evaluators and stakeholder walkthroughs.

**Request:**
Open in web browser: `http://127.0.0.1:8000/demo` (or double click `demo.html`).

**Response (200 OK):**
Returns standalone HTML5 single-page application with Tailwind CSS, live latency metrics, preset links, and responsive cards for all 5 assessment sections.

---

## 2. Analysis Endpoint: `POST /link-analysis`

### A. Example 1: B2B Enterprise SaaS (Illustrative Example)

**Request:**
```bash
curl -X POST "http://127.0.0.1:8000/link-analysis" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://stripe.com"}'
```

**Response (200 OK):**
```json
{
  "success": true,
  "website": "https://stripe.com/",
  "brand": {
    "name": "Stripe",
    "category": "Financial Infrastructure & Payment Processing",
    "summary": "Financial infrastructure platform for businesses of all sizes to accept payments, send payouts, and manage online transactions.",
    "source": "website_content"
  },
  "analysis": {
    "competitor_analysis": {
      "brand_overview": "Global market leader in developer-centric online payment processing and merchant financial services.",
      "business_model": "Usage-based transaction fees, subscription billing for SaaS products, and enterprise merchant interchange revenue.",
      "main_products_or_services": [
        "Stripe Payments",
        "Stripe Billing",
        "Stripe Connect",
        "Stripe Radar (Fraud Prevention)",
        "Stripe Issuing"
      ],
      "competitors": [
        {
          "name": "Adyen",
          "website": "https://adyen.com",
          "description": "Global omnichannel payment gateway tailored for high-volume enterprise retailers and point-of-sale integrations.",
          "strengths": [
            "Unified single-platform architecture for online and in-store POS",
            "Deep European banking footprint and direct acquirer licenses"
          ],
          "weaknesses": [
            "Higher minimum monthly transaction thresholds for early-stage startups",
            "More complex integration onboarding compared to Stripe's instant API keys"
          ],
          "verification_status": "ai_suggested",
          "notes": "Direct global competitor in enterprise digital and physical payments."
        },
        {
          "name": "PayPal Braintree",
          "website": "https://braintreepayments.com",
          "description": "Enterprise merchant payment subsidiary of PayPal providing global card processing and digital wallet integrations.",
          "strengths": [
            "Seamless native consumer integration with PayPal and Venmo balance checkouts",
            "Global brand trust among consumer shoppers"
          ],
          "weaknesses": [
            "Slower developer documentation innovation",
            "Fragmented dashboard tooling across legacy merchant accounts"
          ],
          "verification_status": "ai_suggested",
          "notes": "Competes directly for online checkouts and subscription billing."
        },
        {
          "name": "Square (Block)",
          "website": "https://squareup.com",
          "description": "Small-to-medium business commerce platform combining hardware point-of-sale, payroll, and banking tools.",
          "strengths": [
            "Dominant market share in brick-and-mortar SMB retail and hospitality POS",
            "Turnkey hardware terminals with zero upfront development"
          ],
          "weaknesses": [
            "Less customizable API tooling for complex multi-sided marketplace platforms",
            "Higher blended transaction fees for international corporate cards"
          ],
          "verification_status": "ai_suggested",
          "notes": "Competes in omni-channel retail and SMB payment acceptance."
        }
      ],
      "brand_strengths": [
        "World-class developer experience, client libraries, and documentation",
        "Instant global settlement capabilities with 99.999% platform uptime",
        "Comprehensive unified stack spanning billing, tax compliance, and treasury"
      ],
      "brand_weaknesses": [
        "Higher standard interchange pricing (2.9% + 30c) for low-margin merchants",
        "Automated risk review freezes can impact high-chargeback merchant accounts"
      ],
      "competitive_gaps": [
        "Adyen maintains lower unified acquiring interchange rates for multi-billion retail enterprises."
      ],
      "competitive_advantages": [
        "Gold-standard API ergonomics with zero-downtime versioning",
        "Stripe Connect multi-sided platform architecture powerhouses Shopify, DoorDash, and Lyft"
      ],
      "opportunities": [
        "Accelerating agentic autonomous commerce payment primitives for AI agents and LLM tools",
        "Expanding local payment method orchestration in emerging Latin America and Southeast Asia economies"
      ]
    },
    "target_search_queries": [
      {
        "query": "best global payment gateway for saas billing",
        "platforms": ["Google", "LinkedIn"],
        "intent": "Commercial",
        "business_relevance": "Captures high-growth SaaS founders evaluating recurring billing engines.",
        "target_audience": "CTOs, VP of Finance, and SaaS Founders"
      },
      {
        "query": "how to integrate multi-vendor marketplace payments",
        "platforms": ["Google", "StackOverflow", "GitHub"],
        "intent": "Informational",
        "business_relevance": "Direct acquisition funnel for Stripe Connect platform onboarding.",
        "target_audience": "Staff Software Engineers and Marketplace Architects"
      },
      {
        "query": "automated sales tax compliance for software subscriptions",
        "platforms": ["Google", "LinkedIn"],
        "intent": "Commercial",
        "business_relevance": "Positions Stripe Tax as an all-in-one compliance add-on.",
        "target_audience": "Controllers, CFOs, and Financial Directors"
      },
      {
        "query": "stripe vs adyen enterprise interchange fees",
        "platforms": ["Google", "Reddit"],
        "intent": "Navigational",
        "business_relevance": "Addresses enterprise pricing comparisons during late-stage procurement.",
        "target_audience": "Procurement Specialists and Enterprise Architects"
      },
      {
        "query": "instant merchant payout api integration python",
        "platforms": ["Google", "GitHub"],
        "intent": "Transactional",
        "business_relevance": "Drives immediate API key creation and sandbox testing.",
        "target_audience": "Backend Developers and Engineering Leads"
      }
    ],
    "seo_improvements": {
      "primary_keyword": "payment gateway for businesses",
      "secondary_keywords": [
        "recurring billing software",
        "marketplace payout api",
        "global payment processing",
        "fraud detection software"
      ],
      "long_tail_keywords": [
        "how to automate recurring subscription invoicing for b2b saas",
        "custom payment processing api with built-in fraud prevention"
      ],
      "business_related_keywords": [
        "merchant acquiring",
        "interchange plus pricing",
        "psd2 sca compliance"
      ],
      "recommended_title": "Stripe &mdash; Global Financial Infrastructure & Payment APIs",
      "meta_description": "Accept online payments, automate global recurring billing, send platform payouts, and scale business revenue with Stripe's modern financial APIs.",
      "content_recommendations": [
        "Comprehensive Global Invoicing & Sales Tax Guide by Country",
        "Architecture Blueprint for Building Multi-Sided Gig Economy Platforms"
      ],
      "on_page_improvements": [
        "Incorporate interactive API code snippet toggle directly on the homepage hero",
        "Add explicit enterprise compliance badge carousel (SOC 1/2, PCI-DSS Level 1, ISO 27001)"
      ],
      "technical_seo_suggestions": [
        "Consolidate canonical URLs across localized international country subdomains",
        "Implement Product and Organization JSON-LD structured schema on all product pages"
      ]
    },
    "top_services": [
      {
        "name": "Stripe Payments",
        "description": "Complete payment infrastructure to accept cards, mobile wallets, and 100+ local payment methods online and in person.",
        "target_industry": ["E-Commerce", "SaaS", "Hospitality", "Digital Media"],
        "target_customer": ["Engineering Teams", "E-commerce Founders"],
        "main_benefit": "Maximizes global checkout authorization rates by up to 10.5% with smart card routing.",
        "source": "extracted"
      },
      {
        "name": "Stripe Billing",
        "description": "Subscription and invoice management system supporting tiered, usage-based, and seat-based pricing.",
        "target_industry": ["Software", "Subscription Services"],
        "target_customer": ["SaaS Founders", "Finance Leaders"],
        "main_benefit": "Reduces customer churn with automated smart dunning and card updater technology.",
        "source": "extracted"
      },
      {
        "name": "Stripe Connect",
        "description": "Programmable APIs to onboard, verify KYC, and distribute payouts to vendors and gig workers globally.",
        "target_industry": ["Marketplaces", "Gig Economy", "Crowdfunding Platforms"],
        "target_customer": ["Platform Architects", "Product Managers"],
        "main_benefit": "Handles regulatory compliance and money transmission licensing across 40+ countries.",
        "source": "extracted"
      }
    ],
    "target_audience": {
      "primary_audience": [
        "Chief Technology Officers (CTOs)",
        "Chief Financial Officers (CFOs)",
        "Software Engineering Directors"
      ],
      "secondary_audience": [
        "Full-Stack Web Developers",
        "Product Managers",
        "Treasury and Billing Operations Specialists"
      ],
      "industry_segments": [
        "B2B Software & Cloud Services",
        "Retail E-commerce",
        "Digital Marketplaces & Creator Economy",
        "Fintech & Digital Banking"
      ],
      "business_types": [
        "Venture-Backed Startups",
        "Mid-Market High-Growth Companies",
        "Global Fortune 500 Enterprises"
      ],
      "customer_profiles": [
        "Technical Architect demanding rigorous API uptime and detailed SDKs",
        "Finance Executive seeking unified global multi-currency reconciliation"
      ],
      "geographic_markets": [
        "North America (US, Canada)",
        "European Union & United Kingdom",
        "Asia-Pacific (Australia, Japan, Singapore)",
        "Latin America (Brazil, Mexico)"
      ],
      "customer_needs": [
        "Reliable checkout experiences that eliminate friction and boost conversions",
        "Streamlined regulatory compliance for sales tax, KYC, and PCI data security"
      ],
      "customer_interests": [
        "API Engineering",
        "Microservices Architecture",
        "Fintech Innovation"
      ],
      "marketing_segments": [
        "Enterprise Digital Transformation Accounts",
        "Developer Community & Open-Source Projects",
        "Early-Stage Startup Incubators"
      ],
      "targeting_opportunities": [
        "Sponsor top engineering conferences (PyCon, React Summit, AWS re:Invent)",
        "Run interactive developer tutorials and API sandbox hackathons on GitHub"
      ],
      "source_classification": "website_confirmed"
    }
  },
  "metadata": {
    "pages_analyzed": 5,
    "analysis_model": "gemini-2.0-flash",
    "processing_time_seconds": 1.94
  }
}
```

---

## 3. Error Response Scenarios

### A. SSRF Violation (HTTP 400 Bad Request)
**Trigger**: Passing private IPs, loopback, or non-public addresses.

**Request:**
```bash
curl -X POST "http://127.0.0.1:8000/link-analysis" \
     -H "Content-Type: application/json" \
     -d '{"url": "http://192.168.1.1"}'
```

**Response (400 Bad Request):**
```json
{
  "detail": "Private, loopback, link-local, or cloud metadata IP addresses are not allowed."
}
```

---

### B. Thin / Unreadable Content (HTTP 422 Unprocessable Content)
**Trigger**: Website has less than 100 characters of readable text (e.g. client-side SPA or blank page).

**Request:**
```bash
curl -X POST "http://127.0.0.1:8000/link-analysis" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://blank-spa.example.com"}'
```

**Response (422 Unprocessable Content):**
```json
{
  "detail": "The website at 'https://blank-spa.example.com' did not provide sufficient readable text (18 characters extracted). It may be heavily JavaScript-dependent, password-protected, or empty."
}
```

---

### C. Inaccessible / 404 Website (HTTP 502 Bad Gateway)
**Trigger**: Target website returns 404 Not Found or connection times out.

**Request:**
```bash
curl -X POST "http://127.0.0.1:8000/link-analysis" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://this-domain-does-not-exist-at-all-xyz.com"}'
```

**Response (400 Bad Request):**
```json
{
  "detail": "Hostname 'this-domain-does-not-exist-at-all-xyz.com' could not be resolved."
}
```

---

### D. Missing LLM Configuration (HTTP 503 Service Unavailable)
**Trigger**: `GEMINI_API_KEY` is not supplied in `.env`.

**Response (503 Service Unavailable):**
```json
{
  "detail": "GEMINI_API_KEY is not configured. Please supply a valid Gemini API key in your .env file."
}
```
