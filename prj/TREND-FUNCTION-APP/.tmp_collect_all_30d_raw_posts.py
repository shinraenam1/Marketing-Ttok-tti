import json
from src.collectors.web_meme_collectors import WebMemeCollector

LOOKBACK_DAYS = 30
OUT_PATH = "c:/Users/User/trend-function-app/.tmp_collect_all_30d_raw_posts.json"


def main():
    collector = WebMemeCollector()
    source_docs = collector.collect(
        max_articles_per_source=None,
        lookback_days=LOOKBACK_DAYS,
        include_article_body=False,
    )

    posts = []
    for source, docs in source_docs.items():
        for d in docs:
            posts.append(
                {
                    "source": source,
                    "title": d.get("title", ""),
                    "url": d.get("url", ""),
                    "published_at": d.get("published_at", ""),
                }
            )

    out = {
        "window_days": LOOKBACK_DAYS,
        "total_posts": len(posts),
        "doc_counts": {k: len(v) for k, v in source_docs.items()},
        "posts": posts,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(json.dumps({
        "window_days": LOOKBACK_DAYS,
        "total_posts": len(posts),
        "doc_counts": out["doc_counts"],
        "out_path": OUT_PATH,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
