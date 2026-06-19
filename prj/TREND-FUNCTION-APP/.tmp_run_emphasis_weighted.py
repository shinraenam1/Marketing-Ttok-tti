import json
from src.services.trend_engine import TrendEngine

engine = TrendEngine()
report = engine.generate_meme_report({"lookback_days": 90, "max_results": 20})
out = {
  "source_health": report.get("source_health"),
  "ad_candidate_keywords": report.get("ad_candidate_keywords", [])[:12],
  "trend_keyword_quality": report.get("trend_keyword_quality", {}),
  "top_topics": [
    {
      "topic": t.get("topic"),
      "topic_score": t.get("topic_score"),
      "source_coverage": t.get("source_coverage"),
    }
    for t in report.get("topic_clusters", [])[:8]
  ],
}
with open('.tmp_result_emphasis_weighted.json','w',encoding='utf-8') as f:
    json.dump(out,f,ensure_ascii=False,indent=2)
