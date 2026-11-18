from typing import Literal
from pydantic import BaseModel, Field, HttpUrl

class LinkAnalysisRequest(BaseModel):
    url: HttpUrl = Field(description="Public HTTP or HTTPS website URL to analyze")

class Competitor(BaseModel):
    name: str
    website: str | None = None
    strengths: list[str] = Field(default_factory=list)
    weaknesses_or_gaps: list[str] = Field(default_factory=list)
    verification_status: Literal["verified", "ai_suggested", "unknown"] = "ai_suggested"
    notes: str | None = None

class CompetitorAnalysis(BaseModel):
    brand_overview: str
    competitors: list[Competitor] = Field(default_factory=list)
    brand_strengths: list[str] = Field(default_factory=list)
    competitive_advantages: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)

class SearchQuery(BaseModel):
    query: str
    platforms: list[str] = Field(default_factory=list)
    intent: str
    business_relevance: str
    target_audience: str

class SEOImprovements(BaseModel):
    primary_keyword: str
    secondary_keywords: list[str] = Field(default_factory=list)
    long_tail_keywords: list[str] = Field(default_factory=list)
    recommended_title: str
    meta_description: str
    supporting_content: list[str] = Field(default_factory=list)

class ServiceInsight(BaseModel):
    name: str
    description: str
    target_industry: list[str] = Field(default_factory=list)
    target_customer: list[str] = Field(default_factory=list)
    main_benefit: str
    source: Literal["website", "inferred"] = "website"

class TargetAudience(BaseModel):
    primary_audience: list[str] = Field(default_factory=list)
    secondary_audience: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    business_types: list[str] = Field(default_factory=list)
    customer_profiles: list[str] = Field(default_factory=list)
    geographical_focus: list[str] = Field(default_factory=list)
    customer_needs: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    marketing_segments: list[str] = Field(default_factory=list)

class AnalysisSections(BaseModel):
    competitor_analysis: CompetitorAnalysis
    target_search_queries: list[SearchQuery] = Field(min_length=5, max_length=5)
    seo_improvements: SEOImprovements
    top_services: list[ServiceInsight] = Field(min_length=1, max_length=5)
    target_audience: TargetAudience

class BrandInfo(BaseModel):
    name: str
    category: str
    summary: str
    source: Literal["website_content", "inferred"] = "website_content"

class Metadata(BaseModel):
    pages_analyzed: int
    analysis_model: str
    processing_time_seconds: float

class LinkAnalysisResponse(BaseModel):
    success: bool = True
    website: str
    brand: BrandInfo
    analysis: AnalysisSections
    metadata: Metadata

class ErrorResponse(BaseModel):
    detail: str


class AnalysisPayload(BaseModel):
    brand: BrandInfo
    analysis: AnalysisSections
