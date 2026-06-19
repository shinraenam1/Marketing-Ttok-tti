import json
from src.collectors.web_meme_collectors import WebMemeCollector

collector = WebMemeCollector()
source_docs = collector.collect(max_articles_per_source=5, lookback_days=90, include_article_body=True)

out = {
    "note": "body_text_head in previous dump was truncated preview only",
    "per_source": {},
}

for source, docs in source_docs.items():
    out["per_source"][source] = []
    for d in docs[:3]:
        body = d.get("body_text", "") or ""
        out["per_source"][source].append(
            {
                "title": d.get("title", ""),
                "url": d.get("url", ""),
                "body_text_length": len(body),
                "body_text_preview_500": body[:500],
            }
        )

with open("c:/Users/User/trend-function-app/.tmp_body_size_check.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
