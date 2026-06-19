import json
from src.collectors.web_meme_collectors import WebMemeCollector
from src.services.trend_engine import TrendEngine

collector = WebMemeCollector()
collected = collector.collect(max_articles_per_source=8, lookback_days=90, include_article_body=True)
engine = TrendEngine()
report = engine.generate_meme_report({"lookback_days": 90, "max_results": 20})

out = {
  "source_sizes": {k: len(v) for k, v in collected.items()},
  "wepick_titles": [a.get("title") for a in collected.get("wepick", [])[:5]],
  "ad_candidate_keywords": report.get("ad_candidate_keywords", [])[:10],
  "trend_keyword_quality": report.get("trend_keyword_quality", {}),
}
with open('.tmp_latest_result_with_wepick.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
