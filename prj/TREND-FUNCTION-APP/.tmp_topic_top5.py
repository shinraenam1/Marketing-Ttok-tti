import json
from src.services.trend_engine import TrendEngine

engine = TrendEngine()
report = engine.generate_meme_report({"lookback_days": 90, "max_results": 20})
top5 = sorted(report.get("topic_clusters", []), key=lambda x: x.get("topic_score", 0), reverse=True)[:5]
out = {
    "schema_version": report.get("schema_version"),
    "generated_at": report.get("generated_at"),
    "window_days": report.get("window_days"),
    "source_health": report.get("source_health"),
    "topic_clusters_top5": top5,
}
print(json.dumps(out, ensure_ascii=True, indent=2))
