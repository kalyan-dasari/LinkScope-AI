from typing import Literal
from pydantic import BaseModel, Field, HttpUrl, field_validator

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
    url: HttpUrl = Field(
        description="Public HTTP or HTTPS website URL to analyze",
        examples=["https://example.com"],
    )

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
    brand_overview: str = Field(description="High-level positioning and market category overview")
    business_model: str | None = Field(default=None, description="Identified or inferred business model (e.g. B2B SaaS, Marketplace)")
    main_products_or_services: list[str] = Field(default_factory=list, description="Primary products or services offered by the brand")
    competitors: list[Competitor] = Field(default_factory=list, description="List of at least 3 relevant direct/indirect competitors")
    brand_strengths: list[str] = Field(default_factory=list, description="Core strengths of the analyzed brand")
    brand_weaknesses: list[str] = Field(default_factory=list, description="Noticeable gaps, missing proofs, or weaknesses")
    competitive_gaps: list[str] = Field(default_factory=list, description="Market areas where competitors outperform or have an edge")
    competitive_advantages: list[str] = Field(default_factory=list, description="Unique differentiators, moats, and USPs")
    opportunities: list[str] = Field(default_factory=list, description="Underserved market needs or strategic growth avenues")

    @field_validator(
        "main_products_or_services",
        "brand_strengths",
        "brand_weaknesses",
        "competitive_gaps",
        "competitive_advantages",
        "opportunities",
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
    intent: str = Field(description="Search intent: Informational, Commercial, Transactional, Navigational")
    business_relevance: str = Field(description="Relevance to customer acquisition, pipeline growth, or retention")
    target_audience: str = Field(description="The specific buyer persona or user conducting this search")

    @field_validator("platforms", mode="before")
    @classmethod
    def coerce_platforms(cls, v: object) -> list[str]:
        return _coerce_str_list(v)

# --- SECTION 3: SEO RECOMMENDATIONS ---

class SEOImprovements(BaseModel):
    primary_keyword: str = Field(description="Single highest-priority target keyword")
    secondary_keywords: list[str] = Field(default_factory=list, description="Supporting commercial and topical keywords")
    long_tail_keywords: list[str] = Field(default_factory=list, description="Longer, niche, low-competition query variations")
    business_related_keywords: list[str] = Field(default_factory=list, description="Industry and vertical-specific business keywords")
    recommended_title: str = Field(description="Recommended HTML title tag (50-60 chars, distinguishing from current)")
    meta_description: str = Field(description="Recommended HTML meta description (140-160 chars)")
    content_recommendations: list[str] = Field(default_factory=list, description="Recommended topic clusters, guides, or content hub pages")
    on_page_improvements: list[str] = Field(default_factory=list, description="Actionable on-page optimizations (heading structure, CTAs)")
    technical_seo_suggestions: list[str] = Field(default_factory=list, description="Evidence-backed technical SEO improvements")

    @field_validator(
        "secondary_keywords",
        "long_tail_keywords",
        "business_related_keywords",
        "content_recommendations",
        "on_page_improvements",
        "technical_seo_suggestions",
        mode="before",
    )
    @classmethod
    def coerce_lists(cls, v: object) -> list[str]:
        return _coerce_str_list(v)

# --- SECTION 4: TOP FIVE SERVICES ---

class ServiceInsight(BaseModel):
    name: str = Field(description="Name of service or core product feature")
    description: str = Field(description="Detailed overview of what the service delivers")
    target_industry: list[str] = Field(default_factory=list, description="Target vertical industries")
    target_customer: list[str] = Field(default_factory=list, description="Target customer segment / persona")
    main_benefit: str = Field(description="Primary value proposition or ROI outcome")
    source: Literal["extracted", "inferred", "website", "website_content"] = Field(
        default="extracted",
        description="Whether explicitly extracted from website text or inferred from broader messaging",
    )

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
    business_types: list[str] = Field(default_factory=list, description="Target business types (e.g. B2B, B2C, SMB, Enterprise)")
    customer_profiles: list[str] = Field(default_factory=list, description="Detailed customer personas")
    geographic_markets: list[str] = Field(default_factory=list, description="Regional or international geographic focus")
    customer_needs: list[str] = Field(default_factory=list, description="Core customer pain points and jobs-to-be-done")
    customer_interests: list[str] = Field(default_factory=list, description="Professional or consumer interests")
    marketing_segments: list[str] = Field(default_factory=list, description="Actionable marketing segments")
    targeting_opportunities: list[str] = Field(default_factory=list, description="Recommended channels, positioning, or ABM strategies")
    source_classification: Literal["website_confirmed", "inferred"] = Field(
        default="inferred",
        description="Whether audience details are directly confirmed on-site or inferred",
    )

    @field_validator(
        "primary_audience",
        "secondary_audience",
        "industry_segments",
        "business_types",
        "customer_profiles",
        "geographic_markets",
        "customer_needs",
        "customer_interests",
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
    top_services: list[ServiceInsight] = Field(
        min_length=1,
        max_length=5,
        description="Between 1 and 5 top services or products",
    )
    target_audience: TargetAudience

    @field_validator("target_search_queries", mode="before")
    @classmethod
    def filter_queries(cls, v: object) -> list[object]:
        if isinstance(v, list):
            return [
                item for item in v
                if (isinstance(item, dict) and item.get("query")) or hasattr(item, "query")
            ]
        return v

    @field_validator("top_services", mode="before")
    @classmethod
    def filter_services(cls, v: object) -> list[object]:
        if isinstance(v, list):
            return [
                item for item in v
                if (isinstance(item, dict) and item.get("name")) or hasattr(item, "name")
            ]
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

class ErrorResponse(BaseModel):
    detail: str = Field(description="Human-readable explanation of the error")

class AnalysisPayload(BaseModel):
    brand: BrandInfo
    analysis: AnalysisSections
