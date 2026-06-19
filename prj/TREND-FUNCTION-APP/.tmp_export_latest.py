import json
from src.services.trend_engine import TrendEngine

engine = TrendEngine()
report = engine.generate_meme_report({"lookback_days": 90, "max_results": 20})
out = {
  "generated_at": report.get("generated_at"),
  "window_days": report.get("window_days"),
  "source_health": report.get("source_health"),
  "topic_clusters_top5": report.get("topic_clusters", [])[:5],
  "ad_candidate_keywords": report.get("ad_candidate_keywords", [])[:10],
}
with open('.tmp_latest_result.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
