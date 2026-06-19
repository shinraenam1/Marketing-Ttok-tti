import json
from datetime import datetime, timezone

from src.collectors.web_meme_collectors import WebMemeCollector

LOOKBACK_DAYS = 50
MAX_ARTICLES_PER_SOURCE = 150
OUT_PATH = "c:/Users/User/trend-function-app/.tmp_collect_all_50d_full_posts.json"


def main() -> None:
    collector = WebMemeCollector()
    source_docs = collector.collect(
        max_articles_per_source=MAX_ARTICLES_PER_SOURCE,
        lookback_days=LOOKBACK_DAYS,
        include_article_body=True,
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
                    "excerpt": d.get("excerpt", ""),
                    "body_text": d.get("body_text", ""),
                    "emphasis_text": d.get("emphasis_text", ""),
                    "clean_title": d.get("clean_title", ""),
                    "clean_excerpt": d.get("clean_excerpt", ""),
                    "clean_body_text": d.get("clean_body_text", ""),
                    "clean_emphasis_text": d.get("clean_emphasis_text", ""),
                }
            )

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stage": "stage1_full_posts_raw",
        "window_days": LOOKBACK_DAYS,
        "collection_config": {
            "lookback_days": LOOKBACK_DAYS,
            "collect_all_recent": True,
            "max_articles_per_source": MAX_ARTICLES_PER_SOURCE,
            "include_article_body": True,
        },
        "source_health": {
            "wepick": "ok" if source_docs.get("wepick") else "empty",
            "gogumafarm": "ok" if source_docs.get("gogumafarm") else "empty",
            "careet": "ok" if source_docs.get("careet") else "empty",
        },
        "doc_counts": {k: len(v) for k, v in source_docs.items()},
        "total_posts": len(posts),
        "posts": posts,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(
        json.dumps(
            {
                "window_days": LOOKBACK_DAYS,
                "total_posts": len(posts),
                "doc_counts": out["doc_counts"],
                "out_path": OUT_PATH,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
