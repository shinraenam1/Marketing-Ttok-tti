import json
from src.collectors.web_meme_collectors import WebMemeCollector

collector = WebMemeCollector()
data = collector.collect(max_articles_per_source=8, lookback_days=90, include_article_body=True)
out = {
  "source_sizes": {k: len(v) for k, v in data.items()},
  "wepick_sample": data.get("wepick", [])[:3]
}
with open('.tmp_wepick_check.json','w',encoding='utf-8') as f:
    json.dump(out,f,ensure_ascii=False,indent=2)
