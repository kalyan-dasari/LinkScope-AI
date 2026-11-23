from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator

def _coerce_str_list(v: object) -> list[str]:
    """Coerces strings (newline or comma separated) or single items into a clean list of strings."""
    if isinstance(v, str):
        if "\n" in v:
            return [line.strip("- *•").strip() for line in v.split("\n") if line.strip()]
        if "," in v and not v.startswith("http"):
            parts = [p.strip() for p in v.split(",") if p.strip()]
            if len(parts) > 1:
                return parts
        return [v.strip()] if v.strip() else []
    if isinstance(v, list):
        return [str(item).strip() for item in v if item is not None and str(item).strip()]
    return []

class LinkAnalysisRequest(BaseModel):
    url: str = Field(
        description="Public HTTP or HTTPS website URL to analyze",
        examples=["https://example.com"],
    )

    @field_validator("url")
    @classmethod
    def validate_url_field(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("A valid URL string is required.")
        from urllib.parse import urlparse
        parsed = urlparse(v.strip())
        if parsed.scheme not in ("http", "https"):
            raise ValueError("Only http and https protocols are supported.")
        if not parsed.hostname:
            raise ValueError("URL must contain a valid hostname.")
        # Ensure trailing slash for bare hostnames (e.g. https://example.com -> https://example.com/)
        if not parsed.path or parsed.path == "":
            v = f"{v}/"
        return v

# --- SECTION 1: COMPETITOR VS BRAND ANALYSIS ---

class Competitor(BaseModel):
    name: str = Field(description="Name of the competing business or platform")
    website: str | None = Field(default=None, description="Known or inferred website URL of the competitor")
    description: str = Field(default="", description="Summary of the competitor's core offerings and positioning")
    strengths: list[str] = Field(default_factory=list, description="Key competitor strengths")
    weaknesses: list[str] = Field(default_factory=list, description="Competitor weaknesses or operational gaps")
    verification_status: Literal["verified", "ai_suggested", "unknown"] = Field(
        default="ai_suggested",
        description="Verified if confirmed in evidence, ai_suggested from domain knowledge, unknown if uncertain",
    )
    notes: str | None = Field(default=None, description="Contextual notes on competitive overlap")

    @field_validator("strengths", "weaknesses", mode="before")
    @classmethod
    def coerce_lists(cls, v: object) -> list[str]:
        return _coerce_str_list(v)

    @field_validator("verification_status", mode="before")
    @classmethod
    def coerce_verification_status(cls, v: object) -> str:
        s = str(v).lower()
        if "verif" in s:
            return "verified"
        if "unknown" in s:
            return "unknown"
        return "ai_suggested"

class CompetitorAnalysis(BaseModel):
    brand_name: str | None = Field(default=None, description="Name of the analyzed brand")
    industry_category: str | None = Field(default=None, description="Industry or market category")
    brand_overview: str = Field(description="High-level positioning and market category overview")
    business_model: str | None = Field(default=None, description="Identified or inferred business model (e.g. B2B SaaS, Marketplace)")
    main_products_or_services: list[str] = Field(default_factory=list, description="Primary products or services offered by the brand")
    competitors: list[Competitor] = Field(default_factory=list, description="List of at least 3 relevant direct/indirect competitors")
    brand_strengths: list[str] = Field(default_factory=list, description="Core strengths of the analyzed brand")
    brand_weaknesses: list[str] = Field(default_factory=list, description="Noticeable gaps, missing proofs, or weaknesses")
    competitive_gaps: list[str] = Field(default_factory=list, description="Market areas where competitors outperform or have an edge")
    competitive_advantages: list[str] = Field(default_factory=list, description="Unique differentiators, moats, and USPs")
    opportunities: list[str] = Field(default_factory=list, description="Underserved market needs or strategic growth avenues")
    business_opportunities: list[str] = Field(default_factory=list, description="Alias for opportunities")

    @model_validator(mode="after")
    def sync_aliases(self):
        if not self.business_opportunities and self.opportunities:
            self.business_opportunities = list(self.opportunities)
        elif not self.opportunities and self.business_opportunities:
            self.opportunities = list(self.business_opportunities)
        return self

    @field_validator(
        "main_products_or_services",
        "brand_strengths",
        "brand_weaknesses",
        "competitive_gaps",
        "competitive_advantages",
        "opportunities",
        "business_opportunities",
        mode="before",
    )
    @classmethod
    def coerce_lists(cls, v: object) -> list[str]:
        return _coerce_str_list(v)

    @field_validator("competitors", mode="before")
    @classmethod
    def filter_competitors(cls, v: object) -> list[object]:
        if isinstance(v, list):
            return [
                item for item in v
                if (isinstance(item, dict) and item.get("name")) or hasattr(item, "name")
            ]
        return v

# --- SECTION 2: TOP FIVE TARGET SEARCH QUERIES ---

class SearchQuery(BaseModel):
    query: str = Field(description="High-intent target search query")
    platforms: list[str] = Field(default_factory=list, description="Recommended discovery platforms (e.g. Google, LinkedIn, X, YouTube)")
    recommended_platforms: list[str] = Field(default_factory=list, description="Alias for platforms")
    intent: str = Field(default="Commercial", description="Search intent: Informational, Commercial, Transactional, Navigational")
    search_intent: str | None = Field(default=None, description="Alias for intent")
    business_relevance: str = Field(default="", description="Relevance to customer acquisition, pipeline growth, or retention")
    relevance: str | None = Field(default=None, description="Alias for business_relevance")
    target_audience: str = Field(description="The specific buyer persona or user conducting this search")

    @model_validator(mode="after")
    def sync_aliases(self):
        if not self.search_intent:
            self.search_intent = self.intent
        if not self.intent and self.search_intent:
            self.intent = self.search_intent
        if not self.relevance:
            self.relevance = self.business_relevance
        if not self.business_relevance and self.relevance:
            self.business_relevance = self.relevance
        if not self.recommended_platforms and self.platforms:
            self.recommended_platforms = list(self.platforms)
        if not self.platforms and self.recommended_platforms:
            self.platforms = list(self.recommended_platforms)
        return self

    @field_validator("platforms", "recommended_platforms", mode="before")
    @classmethod
    def coerce_platforms(cls, v: object) -> list[str]:
        return _coerce_str_list(v)

# --- SECTION 3: SEO RECOMMENDATIONS ---

class SEOImprovements(BaseModel):
    primary_keyword: str = Field(description="Single highest-priority target keyword")
    primary_keywords: list[str] = Field(default_factory=list, description="List representation of primary keywords")
    secondary_keywords: list[str] = Field(default_factory=list, description="Supporting commercial and topical keywords")
    long_tail_keywords: list[str] = Field(default_factory=list, description="Longer, niche, low-competition query variations")
    business_related_keywords: list[str] = Field(default_factory=list, description="Industry and vertical-specific business keywords")
    recommended_title: str = Field(description="Recommended HTML title tag (50-60 chars, distinguishing from current)")
    suggested_seo_title: str | None = Field(default=None, description="Alias for recommended_title")
    meta_description: str = Field(description="Recommended HTML meta description (140-160 chars)")
    suggested_meta_description: str | None = Field(default=None, description="Alias for meta_description")
    content_recommendations: list[str] = Field(default_factory=list, description="Recommended topic clusters, guides, or content hub pages")
    on_page_improvements: list[str] = Field(default_factory=list, description="Actionable on-page optimizations (heading structure, CTAs)")
    on_page_seo_improvements: list[str] = Field(default_factory=list, description="Alias for on_page_improvements")
    technical_seo_suggestions: list[str] = Field(default_factory=list, description="Evidence-backed technical SEO improvements")

    @model_validator(mode="after")
    def sync_aliases(self):
        if not self.suggested_seo_title:
            self.suggested_seo_title = self.recommended_title
        if not self.recommended_title and self.suggested_seo_title:
            self.recommended_title = self.suggested_seo_title
        if not self.suggested_meta_description:
            self.suggested_meta_description = self.meta_description
        if not self.meta_description and self.suggested_meta_description:
            self.meta_description = self.suggested_meta_description
        if not self.primary_keywords and self.primary_keyword:
            self.primary_keywords = [self.primary_keyword]
        if not self.on_page_seo_improvements and self.on_page_improvements:
            self.on_page_seo_improvements = list(self.on_page_improvements)
        if not self.on_page_improvements and self.on_page_seo_improvements:
            self.on_page_improvements = list(self.on_page_seo_improvements)
        return self

    @field_validator(
        "primary_keywords",
        "secondary_keywords",
        "long_tail_keywords",
        "business_related_keywords",
        "content_recommendations",
        "on_page_improvements",
        "on_page_seo_improvements",
        "technical_seo_suggestions",
        mode="before",
    )
    @classmethod
    def coerce_lists(cls, v: object) -> list[str]:
        return _coerce_str_list(v)

# --- SECTION 4: TOP FIVE SERVICES ---

class ServiceInsight(BaseModel):
    name: str = Field(description="Name of service or core product feature")
    service_name: str | None = Field(default=None, description="Alias for name")
    description: str = Field(description="Detailed overview of what the service delivers")
    target_industry: list[str] = Field(default_factory=list, description="Target vertical industries")
    target_customer: list[str] = Field(default_factory=list, description="Target customer segment / persona")
    main_benefit: str = Field(description="Primary value proposition or ROI outcome")
    source: Literal["extracted", "inferred", "website", "website_content"] = Field(
        default="extracted",
        description="Whether explicitly extracted from website text or inferred from broader messaging",
    )

    @model_validator(mode="after")
    def sync_aliases(self):
        if not self.service_name:
            self.service_name = self.name
        if not self.name and self.service_name:
            self.name = self.service_name
        return self

    @field_validator("target_industry", "target_customer", mode="before")
    @classmethod
    def coerce_lists(cls, v: object) -> list[str]:
        return _coerce_str_list(v)

    @field_validator("source", mode="before")
    @classmethod
    def coerce_source(cls, v: object) -> str:
        s = str(v).lower()
        if "infer" in s:
            return "inferred"
        return "extracted"

# --- SECTION 5: TARGET AUDIENCE ---

class TargetAudience(BaseModel):
    primary_audience: list[str] = Field(default_factory=list, description="Core decision-makers and economic buyers")
    secondary_audience: list[str] = Field(default_factory=list, description="Influencers, end-users, or technical evaluators")
    industry_segments: list[str] = Field(default_factory=list, description="Target industry verticals")
    target_industry: list[str] = Field(default_factory=list, description="Alias for industry_segments")
    business_types: list[str] = Field(default_factory=list, description="Target business types (e.g. B2B, B2C, SMB, Enterprise)")
    business_type: list[str] = Field(default_factory=list, description="Alias for business_types")
    customer_profiles: list[str] = Field(default_factory=list, description="Detailed customer personas")
    customer_profile: list[str] = Field(default_factory=list, description="Alias for customer_profiles")
    geographic_markets: list[str] = Field(default_factory=list, description="Regional or international geographic focus")
    geographical_markets: list[str] = Field(default_factory=list, description="Alias for geographic_markets")
    customer_needs: list[str] = Field(default_factory=list, description="Core customer pain points and jobs-to-be-done")
    customer_pain_points_or_needs: list[str] = Field(default_factory=list, description="Alias for customer_needs")
    customer_interests: list[str] = Field(default_factory=list, description="Professional or consumer interests")
    interests: list[str] = Field(default_factory=list, description="Alias for customer_interests")
    marketing_segments: list[str] = Field(default_factory=list, description="Actionable marketing segments")
    targeting_opportunities: list[str] = Field(default_factory=list, description="Recommended channels, positioning, or ABM strategies")
    source_classification: Literal["website_confirmed", "inferred"] = Field(
        default="inferred",
        description="Whether audience details are directly confirmed on-site or inferred",
    )

    @model_validator(mode="after")
    def sync_aliases(self):
        if not self.target_industry and self.industry_segments:
            self.target_industry = list(self.industry_segments)
        if not self.industry_segments and self.target_industry:
            self.industry_segments = list(self.target_industry)
        if not self.business_type and self.business_types:
            self.business_type = list(self.business_types)
        if not self.business_types and self.business_type:
            self.business_types = list(self.business_type)
        if not self.customer_profile and self.customer_profiles:
            self.customer_profile = list(self.customer_profiles)
        if not self.customer_profiles and self.customer_profile:
            self.customer_profiles = list(self.customer_profile)
        if not self.geographical_markets and self.geographic_markets:
            self.geographical_markets = list(self.geographic_markets)
        if not self.geographic_markets and self.geographical_markets:
            self.geographic_markets = list(self.geographical_markets)
        if not self.customer_pain_points_or_needs and self.customer_needs:
            self.customer_pain_points_or_needs = list(self.customer_needs)
        if not self.customer_needs and self.customer_pain_points_or_needs:
            self.customer_needs = list(self.customer_pain_points_or_needs)
        if not self.interests and self.customer_interests:
            self.interests = list(self.customer_interests)
        if not self.customer_interests and self.interests:
            self.customer_interests = list(self.interests)
        return self

    @field_validator(
        "primary_audience",
        "secondary_audience",
        "industry_segments",
        "target_industry",
        "business_types",
        "business_type",
        "customer_profiles",
        "customer_profile",
        "geographic_markets",
        "geographical_markets",
        "customer_needs",
        "customer_pain_points_or_needs",
        "customer_interests",
        "interests",
        "marketing_segments",
        "targeting_opportunities",
        mode="before",
    )
    @classmethod
    def coerce_lists(cls, v: object) -> list[str]:
        return _coerce_str_list(v)

    @field_validator("source_classification", mode="before")
    @classmethod
    def coerce_source_classification(cls, v: object) -> str:
        s = str(v).lower()
        if "confirm" in s or "verif" in s or "site" in s:
            return "website_confirmed"
        return "inferred"

# --- COMPOSITE SCHEMAS ---

class AnalysisSections(BaseModel):
    competitor_analysis: CompetitorAnalysis
    target_search_queries: list[SearchQuery] = Field(
        min_length=5,
        max_length=5,
        description="Exactly 5 targeted high-impact search queries",
    )
    seo_improvements: SEOImprovements
    seo_recommendations: SEOImprovements | None = Field(default=None, description="Alias for seo_improvements")
    top_services: list[ServiceInsight] = Field(
        min_length=1,
        max_length=5,
        description="Between 1 and 5 top services or products",
    )
    target_audience: TargetAudience

    @model_validator(mode="after")
    def sync_aliases(self):
        if self.seo_recommendations is None:
            self.seo_recommendations = self.seo_improvements
        return self

    @field_validator("target_search_queries", mode="before")
    @classmethod
    def filter_queries(cls, v: object) -> list[object]:
        if isinstance(v, list):
            valid = [
                item for item in v
                if (isinstance(item, dict) and item.get("query")) or hasattr(item, "query")
            ]
            if len(valid) > 5:
                return valid[:5]
            return valid
        return v

    @field_validator("top_services", mode="before")
    @classmethod
    def filter_services(cls, v: object) -> list[object]:
        if isinstance(v, list):
            valid = [
                item for item in v
                if (isinstance(item, dict) and item.get("name")) or hasattr(item, "name")
            ]
            if len(valid) > 5:
                return valid[:5]
            return valid
        return v

class BrandInfo(BaseModel):
    name: str = Field(description="Brand or company name")
    category: str = Field(description="Industry or market category")
    summary: str = Field(description="Concise description of what the company does")
    source: Literal["website_content", "inferred"] = Field(default="website_content")

    @field_validator("source", mode="before")
    @classmethod
    def coerce_brand_source(cls, v: object) -> str:
        s = str(v).lower()
        if "infer" in s:
            return "inferred"
        return "website_content"

class Metadata(BaseModel):
    pages_analyzed: int = Field(description="Total pages crawled and evaluated")
    analysis_model: str = Field(description="AI model utilized for analysis")
    processing_time_seconds: float = Field(description="Total end-to-end processing latency in seconds")

class LinkAnalysisResponse(BaseModel):
    success: bool = True
    website: str
    brand: BrandInfo
    analysis: AnalysisSections
    metadata: Metadata

    # Direct top-level access to the 5 core assessment sections
    # Ensures compatibility with test suites checking root keys or nested keys
    competitor_analysis: CompetitorAnalysis | None = None
    target_search_queries: list[SearchQuery] | None = None
    seo_recommendations: SEOImprovements | None = None
    top_services: list[ServiceInsight] | None = None
    target_audience: TargetAudience | None = None

    @model_validator(mode="after")
    def populate_root_sections(self):
        if self.analysis:
            if self.competitor_analysis is None:
                self.competitor_analysis = self.analysis.competitor_analysis
            if self.target_search_queries is None:
                self.target_search_queries = self.analysis.target_search_queries
            if self.seo_recommendations is None:
                self.seo_recommendations = self.analysis.seo_improvements
            if self.top_services is None:
                self.top_services = self.analysis.top_services
            if self.target_audience is None:
                self.target_audience = self.analysis.target_audience
        return self

class ErrorResponse(BaseModel):
    detail: str = Field(description="Human-readable explanation of the error")

class AnalysisPayload(BaseModel):
    brand: BrandInfo
    analysis: AnalysisSections
