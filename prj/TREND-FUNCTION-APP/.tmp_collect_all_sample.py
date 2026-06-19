import json
from src.collectors.web_meme_collectors import WebMemeCollector

collector = WebMemeCollector()
source_docs = collector.collect(max_articles_per_source=None, lookback_days=90, include_article_body=True)

out = {
    "mode": {"lookback_days": 90, "collect_all_recent": True},
    "counts": {k: len(v) for k, v in source_docs.items()},
    "samples": {},
}

for source, docs in source_docs.items():
    out["samples"][source] = [
        {
            "title": d.get("title", ""),
            "url": d.get("url", ""),
            "published_at": d.get("published_at", ""),
            "body_head": (d.get("body_text", "") or "")[:220],
        }
        for d in docs[:3]
    ]

with open("c:/Users/User/trend-function-app/.tmp_collect_all_sample.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
