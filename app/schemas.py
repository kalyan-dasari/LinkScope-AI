from typing import Literal
from pydantic import BaseModel, Field, HttpUrl

class LinkAnalysisRequest(BaseModel):
    url: HttpUrl = Field(
        description="Public HTTP or HTTPS website URL to analyze",
        examples=["https://example.com"],
    )

class Competitor(BaseModel):
    name: str = Field(description="Name of the competing business or platform")
    website: str | None = Field(default=None, description="Known or inferred website URL of the competitor")
    strengths: list[str] = Field(default_factory=list, description="Key competitor strengths")
    weaknesses_or_gaps: list[str] = Field(default_factory=list, description="Competitor weaknesses or market gaps")
    verification_status: Literal["verified", "ai_suggested", "unknown"] = Field(
        default="ai_suggested",
        description="Verified if found in source text, ai_suggested if inferred from domain knowledge",
    )
    notes: str | None = Field(default=None, description="Contextual notes on competitive overlap")

class CompetitorAnalysis(BaseModel):
    brand_overview: str = Field(description="High-level positioning and market category overview")
    competitors: list[Competitor] = Field(default_factory=list, description="List of direct and indirect competitors")
    brand_strengths: list[str] = Field(default_factory=list, description="Core strengths of the analyzed brand")
    competitive_advantages: list[str] = Field(default_factory=list, description="Unique differentiators and moats")
    opportunities: list[str] = Field(default_factory=list, description="Market opportunities and underserved needs")

class SearchQuery(BaseModel):
    query: str = Field(description="High-intent search query")
    platforms: list[str] = Field(default_factory=list, description="Platforms relevant to this query (e.g. Google, LinkedIn, X)")
    intent: str = Field(description="Search intent: Informational, Commercial, Transactional, Navigational")
    business_relevance: str = Field(description="Why this query matters for customer acquisition or retention")
    target_audience: str = Field(description="The customer persona conducting this search")

class SEOImprovements(BaseModel):
    primary_keyword: str = Field(description="Single highest-priority target keyword")
    secondary_keywords: list[str] = Field(default_factory=list, description="Supporting commercial and topical keywords")
    long_tail_keywords: list[str] = Field(default_factory=list, description="Longer, niche, low-competition phrases")
    recommended_title: str = Field(description="Recommended HTML title tag (50-60 chars)")
    meta_description: str = Field(description="Recommended HTML meta description (140-160 chars)")
    supporting_content: list[str] = Field(default_factory=list, description="Recommended blog topics or content hub pages")

class ServiceInsight(BaseModel):
    name: str = Field(description="Name of service or core product feature")
    description: str = Field(description="Detailed overview of what the service delivers")
    target_industry: list[str] = Field(default_factory=list, description="Target vertical industries")
    target_customer: list[str] = Field(default_factory=list, description="Target customer segment")
    main_benefit: str = Field(description="Primary value proposition or ROI outcome")
    source: Literal["website", "inferred"] = Field(default="website", description="Whether explicitly listed or inferred")

class TargetAudience(BaseModel):
    primary_audience: list[str] = Field(default_factory=list, description="Core decision-makers and buyers")
    secondary_audience: list[str] = Field(default_factory=list, description="Influencers, end-users, or tertiary beneficiaries")
    industries: list[str] = Field(default_factory=list, description="Target industry verticals")
    business_types: list[str] = Field(default_factory=list, description="Target business types (e.g. B2B, B2C, SMB, Enterprise)")
    customer_profiles: list[str] = Field(default_factory=list, description="Archetypal customer personas")
    geographical_focus: list[str] = Field(default_factory=list, description="Regional or geographic focus")
    customer_needs: list[str] = Field(default_factory=list, description="Core problems or jobs-to-be-done")
    interests: list[str] = Field(default_factory=list, description="Professional or consumer interests")
    marketing_segments: list[str] = Field(default_factory=list, description="Actionable marketing segments")

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

class BrandInfo(BaseModel):
    name: str = Field(description="Brand or company name")
    category: str = Field(description="Industry or market category")
    summary: str = Field(description="Concise description of what the company does")
    source: Literal["website_content", "inferred"] = Field(default="website_content")

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
