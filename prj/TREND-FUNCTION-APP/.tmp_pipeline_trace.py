import json
from src.collectors.web_meme_collectors import WebMemeCollector
from src.services.scoring import extract_meme_candidates
from src.services.trend_engine import TrendEngine

lookback_days = 90
collector = WebMemeCollector()
source_docs = collector.collect(max_articles_per_source=12, lookback_days=lookback_days, include_article_body=True)
all_docs = [d for docs in source_docs.values() for d in docs]

stage1 = {
    "source_counts": {k: len(v) for k, v in source_docs.items()},
    "sample_urls": {k: [x.get("url", "") for x in v[:3]] for k, v in source_docs.items()},
}

emphasis_docs = [d for d in all_docs if (d.get("clean_emphasis_text") or "").strip()]
stage2 = {
    "total_documents": len(all_docs),
    "documents_with_emphasis": len(emphasis_docs),
    "sample_cleaned": [
        {
            "source": d.get("source"),
            "title": d.get("title"),
            "clean_title": (d.get("clean_title") or "")[:120],
            "clean_emphasis_text": (d.get("clean_emphasis_text") or "")[:120],
        }
        for d in all_docs[:5]
    ],
}

meme_candidates = extract_meme_candidates(all_docs, top_k=20)
stage3 = {
    "candidate_count": len(meme_candidates),
    "top_candidates": meme_candidates[:10],
}

engine = TrendEngine()
report = engine.generate_meme_report({"lookback_days": lookback_days, "max_results": 20})

stage4 = {
    "cluster_count": len(report.get("topic_clusters", [])),
    "top_clusters": [
        {
            "topic": t.get("topic"),
            "topic_score": t.get("topic_score"),
            "growth_rate_pct": t.get("growth_rate_pct"),
            "source_coverage": t.get("source_coverage"),
            "summary": (t.get("summary") or "")[:220],
        }
        for t in report.get("topic_clusters", [])[:8]
    ],
}

stage5 = {
    "ad_candidate_keywords": report.get("ad_candidate_keywords", []),
    "trend_keyword_quality": report.get("trend_keyword_quality", {}),
    "source_health": report.get("source_health", {}),
}

out = {
    "generated_at": report.get("generated_at"),
    "window_days": lookback_days,
    "pipeline_stages": {
        "stage1_crawl": stage1,
        "stage2_cleaning_and_emphasis": stage2,
        "stage3_candidate_scoring": stage3,
        "stage4_topic_clustering": stage4,
        "stage5_final_output": stage5,
    },
}

with open("c:/Users/User/trend-function-app/.tmp_pipeline_trace.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
