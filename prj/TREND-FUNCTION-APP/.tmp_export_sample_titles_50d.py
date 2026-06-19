import json
from pathlib import Path

FULL_PATH = Path("c:/Users/User/trend-function-app/.tmp_collect_all_50d_full_posts.json")
KEYWORD_PATH = Path("c:/Users/User/trend-function-app/.tmp_major_keywords_50d.json")
OUT_PATH = Path("c:/Users/User/trend-function-app/.tmp_sample_titles_50d_full.json")


def main() -> None:
    full_data = json.loads(FULL_PATH.read_text(encoding="utf-8"))
    kw_data = json.loads(KEYWORD_PATH.read_text(encoding="utf-8"))

    posts = full_data.get("posts", [])
    major_keywords = kw_data.get("major_keywords", [])

    all_titles = []
    for p in posts:
        all_titles.append(
            {
                "source": p.get("source", ""),
                "published_at": p.get("published_at", ""),
                "title": p.get("title", ""),
                "url": p.get("url", ""),
            }
        )

    keyword_sample_titles = []
    for item in major_keywords:
        keyword_sample_titles.append(
            {
                "keyword": item.get("keyword", ""),
                "post_count": item.get("post_count", 0),
                "sample_titles": item.get("sample_titles", []),
            }
        )

    out = {
        "window_days": full_data.get("window_days", 50),
        "total_posts": full_data.get("total_posts", len(all_titles)),
        "doc_counts": full_data.get("doc_counts", {}),
        "major_keywords_sample_titles": keyword_sample_titles,
        "all_post_titles": all_titles,
    }

    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    preview = {
        "out_path": str(OUT_PATH),
        "total_posts": out["total_posts"],
        "doc_counts": out["doc_counts"],
        "major_keywords_sample_titles_top5": out["major_keywords_sample_titles"][:5],
    }
    print(json.dumps(preview, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
