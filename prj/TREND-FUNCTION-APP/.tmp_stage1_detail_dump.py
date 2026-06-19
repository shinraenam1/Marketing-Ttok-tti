import json
from src.collectors.web_meme_collectors import WebMemeCollector

collector = WebMemeCollector()
source_docs = collector.collect(max_articles_per_source=6, lookback_days=90, include_article_body=True)

dump = {
    "stage": "stage1_detail_page_scrape_raw",
    "source_counts": {k: len(v) for k, v in source_docs.items()},
    "sources": {},
}

for source, docs in source_docs.items():
    dump["sources"][source] = []
    for d in docs[:3]:
        dump["sources"][source].append(
            {
                "title": d.get("title", ""),
                "url": d.get("url", ""),
                "published_at": d.get("published_at", ""),
                "excerpt": d.get("excerpt", "")[:220],
                "body_text_head": d.get("body_text", "")[:380],
                "emphasis_text": d.get("emphasis_text", "")[:220],
            }
        )

with open("c:/Users/User/trend-function-app/.tmp_stage1_detail_dump.json", "w", encoding="utf-8") as f:
    json.dump(dump, f, ensure_ascii=False, indent=2)
