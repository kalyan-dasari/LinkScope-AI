import asyncio
from app.services.analysis_service import analyze_website

async def test():
    print("Testing end-to-end analyze_website('https://example.com')...")
    response = await analyze_website("https://example.com")
    print("\n================= FULL REAL-WORLD VERIFICATION =================")
    print(f"Success: {response.success}")
    print(f"Target Website: {response.website}")
    print(f"Brand Name: {response.brand.name} ({response.brand.category})")
    print(f"Brand Summary: {response.brand.summary}")
    print(f"\n1. Competitor Analysis ({len(response.analysis.competitor_analysis.competitors)} competitors):")
    for c in response.analysis.competitor_analysis.competitors:
        print(f"   - {c.name} (Status: {c.verification_status}): {c.description}")
        print(f"     Strengths: {c.strengths}")
        print(f"     Weaknesses: {c.weaknesses}")
    print(f"   Brand Strengths: {response.analysis.competitor_analysis.brand_strengths}")
    print(f"   Competitive Advantages: {response.analysis.competitor_analysis.competitive_advantages}")
    print(f"   Opportunities: {response.analysis.competitor_analysis.opportunities}")

    print(f"\n2. Top Search Queries ({len(response.analysis.target_search_queries)} queries):")
    for q in response.analysis.target_search_queries:
        print(f"   - Query: '{q.query}'")
        print(f"     Platforms: {q.platforms} | Intent: {q.intent} | Audience: {q.target_audience}")

    print(f"\n3. SEO Recommendations:")
    print(f"   Primary Keyword: {response.analysis.seo_improvements.primary_keyword}")
    print(f"   Secondary Keywords: {response.analysis.seo_improvements.secondary_keywords}")
    print(f"   Recommended Title: {response.analysis.seo_improvements.recommended_title}")
    print(f"   Meta Description: {response.analysis.seo_improvements.meta_description}")
    print(f"   On-Page Improvements: {response.analysis.seo_improvements.on_page_improvements}")

    print(f"\n4. Top Services ({len(response.analysis.top_services)} services):")
    for s in response.analysis.top_services:
        print(f"   - {s.name} (Source: {s.source}): {s.description}")
        print(f"     Benefit: {s.main_benefit}")

    print(f"\n5. Target Audience:")
    print(f"   Primary Audience: {response.analysis.target_audience.primary_audience}")
    print(f"   Secondary Audience: {response.analysis.target_audience.secondary_audience}")
    print(f"   Industries: {response.analysis.target_audience.industry_segments}")
    print(f"   Needs: {response.analysis.target_audience.customer_needs}")
    print(f"   Source Classification: {response.analysis.target_audience.source_classification}")

    print(f"\nTelemetry & Metadata:")
    print(f"   Pages Analyzed: {response.metadata.pages_analyzed}")
    print(f"   Active Model: {response.metadata.analysis_model}")
    print(f"   End-to-End Processing Time: {response.metadata.processing_time_seconds} seconds")
    print("=================================================================\n")

if __name__ == "__main__":
    asyncio.run(test())
