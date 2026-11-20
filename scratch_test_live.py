import asyncio
from app.services.analysis_service import analyze_website

async def test():
    print("Testing live analyze_website on https://www.studearning.tech/ ...")
    res = await analyze_website("https://www.studearning.tech/")
    print("\n--- LIVE TEST SUCCESS! ---")
    print("Website:", res.website)
    print("Brand Name:", res.brand.name)
    print("Brand Category:", res.brand.category)
    print("Brand Summary:", res.brand.summary)
    print(f"Competitors count: {len(res.analysis.competitor_analysis.competitors)}")
    for c in res.analysis.competitor_analysis.competitors:
        print(f"  - {c.name} ({c.verification_status}): {c.description[:80]}...")
    print(f"Target Search Queries count: {len(res.analysis.target_search_queries)}")
    for q in res.analysis.target_search_queries:
        print(f"  - [{q.intent}] '{q.query}' on {q.platforms}")
    print("SEO Recommended Title:", res.analysis.seo_improvements.recommended_title)
    print("SEO Primary Keyword:", res.analysis.seo_improvements.primary_keyword)
    print(f"Top Services count: {len(res.analysis.top_services)}")
    for s in res.analysis.top_services:
        print(f"  - {s.name} ({s.source}): {s.description[:80]}...")
    print("Target Audience Primary:", res.analysis.target_audience.primary_audience)
    print("Target Audience Needs:", res.analysis.target_audience.customer_needs)
    print("Metadata Pages Analyzed:", res.metadata.pages_analyzed)
    print("Metadata Model:", res.metadata.analysis_model)
    print(f"Processing Time: {res.metadata.processing_time_seconds}s")

if __name__ == "__main__":
    asyncio.run(test())
