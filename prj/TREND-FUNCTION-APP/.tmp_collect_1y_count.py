import json
from src.collectors.web_meme_collectors import WebMemeCollector

collector = WebMemeCollector()
source_docs = collector.collect(max_articles_per_source=None, lookback_days=365, include_article_body=False)
counts = {k: len(v) for k, v in source_docs.items()}

out = {
    "lookback_days": 365,
    "counts": counts,
    "total": sum(counts.values()),
}

with open("c:/Users/User/trend-function-app/.tmp_collect_1y_count.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
