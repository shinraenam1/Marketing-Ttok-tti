import json
from src.collectors.web_meme_collectors import WebMemeCollector

collector = WebMemeCollector()
source_docs = collector.collect(max_articles_per_source=10, lookback_days=90, include_article_body=True)

out = {
    "stage": "stage1_detail_page_scrape_raw",
    "source_counts": {k: len(v) for k, v in source_docs.items()},
    "samples": {},
}

for source, docs in source_docs.items():
    out["samples"][source] = [
        {
            "title": d.get("title", ""),
            "url": d.get("url", ""),
            "published_at": d.get("published_at", ""),
            "excerpt": (d.get("excerpt", "") or "")[:160],
            "body_text_head": (d.get("body_text", "") or "")[:260],
            "emphasis_text": (d.get("emphasis_text", "") or "")[:180],
        }
        for d in docs[:5]
    ]

with open("c:/Users/User/trend-function-app/.tmp_stage1_detail_dump_5.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
