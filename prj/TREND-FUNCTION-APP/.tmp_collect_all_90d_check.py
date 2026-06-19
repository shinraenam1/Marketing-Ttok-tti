import json
from src.collectors.web_meme_collectors import WebMemeCollector
from src.services.trend_engine import TrendEngine

engine = TrendEngine()
report = engine.generate_meme_report({"lookback_days": 90, "collect_all_recent": True, "max_results": 20})

collector = WebMemeCollector()
source_docs = collector.collect(max_articles_per_source=None, lookback_days=90, include_article_body=False)

out = {
    "source_health": report.get("source_health", {}),
    "collection_config": report.get("collection_config", {}),
    "doc_counts": {k: len(v) for k, v in source_docs.items()},
}

with open("c:/Users/User/trend-function-app/.tmp_collect_all_90d_check.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
