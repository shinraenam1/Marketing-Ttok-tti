import json
from pathlib import Path

IN_PATH = Path("c:/Users/User/trend-function-app/.tmp_major_keywords_50d_all_posts.json")
OUT_PATH = Path("c:/Users/User/trend-function-app/.tmp_major_keywords_50d_sample_titles.json")


def main() -> None:
    data = json.loads(IN_PATH.read_text(encoding="utf-8"))
    major_keywords = data.get("major_keywords", [])

    formatted = []
    for item in major_keywords:
        posts = item.get("all_related_posts", [])
        sample_titles = []
        for p in posts[:3]:
            title = str(p.get("title", "")).strip()
            if title:
                sample_titles.append(title)

        formatted.append(
            {
                "keyword": item.get("keyword", ""),
                "post_count": item.get("post_count", 0),
                "sample_titles": sample_titles,
            }
        )

    out = {
        "window_days": data.get("window_days"),
        "total_posts": data.get("total_posts"),
        "doc_counts": data.get("doc_counts", {}),
        "major_keywords": formatted,
    }

    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    preview = {
        "out_path": str(OUT_PATH),
        "top5": out["major_keywords"][:5],
    }
    print(json.dumps(preview, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
