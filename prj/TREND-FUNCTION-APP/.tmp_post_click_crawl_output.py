import json
from src.collectors.web_meme_collectors import WebMemeCollector
from src.services.trend_engine import TrendEngine

collector = WebMemeCollector()
collected = collector.collect(max_articles_per_source=6, lookback_days=90, include_article_body=True)

engine = TrendEngine()
report = engine.generate_meme_report({"lookback_days": 90, "max_results": 10})

out = {
  "crawl_check": {
    "source_sizes": {k: len(v) for k, v in collected.items()},
    "samples": {
      k: [
        {
          "title": d.get("title"),
          "published_at": d.get("published_at"),
          "emphasis_text": d.get("emphasis_text", "")[:120]
        }
        for d in v[:2]
      ]
      for k, v in collected.items()
    }
  },
  "report_output": {
    "source_health": report.get("source_health"),
    "ad_candidate_keywords": report.get("ad_candidate_keywords", [])[:8],
    "topic_clusters_top3": [
      {
        "topic": t.get("topic"),
        "summary": t.get("summary", "")[:240]
      }
      for t in report.get("topic_clusters", [])[:3]
    ]
  }
}

with open('.tmp_post_click_crawl_output.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
