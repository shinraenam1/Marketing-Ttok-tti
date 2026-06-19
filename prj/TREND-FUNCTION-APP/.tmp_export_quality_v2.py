import json
from src.services.trend_engine import TrendEngine

engine = TrendEngine()
report = engine.generate_meme_report({"lookback_days": 90, "max_results": 20})
out = {
  "source_health": report.get("source_health"),
  "ad_candidate_keywords": report.get("ad_candidate_keywords", [])[:10],
  "trend_keyword_quality": report.get("trend_keyword_quality", {}),
}
with open('.tmp_latest_result_quality_v2.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
