import json
from src.collectors.web_meme_collectors import WebMemeCollector
from src.services.trend_engine import TrendEngine

collector = WebMemeCollector()
source_docs = collector.collect(max_articles_per_source=8, lookback_days=90, include_article_body=True)
all_docs = [d for docs in source_docs.values() for d in docs]

doc_samples = []
for d in all_docs[:5]:
    doc_samples.append({
        "source": d.get("source"),
        "title": d.get("title"),
        "clean_title": d.get("clean_title"),
        "excerpt": (d.get("excerpt") or "")[:180],
        "clean_excerpt": (d.get("clean_excerpt") or "")[:180],
        "body_text_preview": (d.get("body_text") or "")[:220],
        "clean_body_preview": (d.get("clean_body_text") or "")[:220],
        "published_at": d.get("published_at"),
        "url": d.get("url"),
    })

engine = TrendEngine()
report = engine.generate_meme_report({"lookback_days": 90, "max_results": 20})
top5 = sorted(report.get("topic_clusters", []), key=lambda x: x.get("topic_score", 0), reverse=True)[:5]

out = {
    "generated_at": report.get("generated_at"),
    "window_days": report.get("window_days"),
    "source_health": report.get("source_health"),
    "doc_samples_with_clean_fields": doc_samples,
    "topic_clusters_top5": top5,
}
print(json.dumps(out, ensure_ascii=True, indent=2))
