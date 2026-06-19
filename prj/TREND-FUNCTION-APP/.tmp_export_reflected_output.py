import json
from src.services.trend_engine import TrendEngine

engine = TrendEngine()
report = engine.generate_meme_report({"lookback_days": 90, "max_results": 20})

out = {
  "generated_at": report.get("generated_at"),
  "window_days": report.get("window_days"),
  "source_health": report.get("source_health"),
  "trend_keyword_quality": report.get("trend_keyword_quality"),
  "ad_candidate_keywords": report.get("ad_candidate_keywords", [])[:10],
  "topic_clusters_top5": [
    {
      "topic": t.get("topic"),
      "topic_score": t.get("topic_score"),
      "growth_rate_pct": t.get("growth_rate_pct"),
      "source_coverage": t.get("source_coverage"),
      "sample_title": (t.get("sample_contents") or [{}])[0].get("title", "")
    }
    for t in report.get("topic_clusters", [])[:5]
  ]
}

with open('.tmp_latest_reflected_output.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
