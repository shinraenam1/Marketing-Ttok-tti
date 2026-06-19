import json
from pathlib import Path

SRC_FULL = Path("c:/Users/User/trend-function-app/.tmp_collect_all_50d_full_posts.json")
SRC_KW = Path("c:/Users/User/trend-function-app/.tmp_major_keywords_50d_sample_titles.json")
OUT = Path("c:/Users/User/trend-function-app/.tmp_final_report_50d.json")


def _short_summary(text: str, max_len: int = 240) -> str:
    s = " ".join((text or "").replace("\n", " ").split())
    if len(s) <= max_len:
        return s
    return s[: max_len - 1].rstrip() + "…"


def main() -> None:
    full_data = json.loads(SRC_FULL.read_text(encoding="utf-8"))
    kw_data = json.loads(SRC_KW.read_text(encoding="utf-8"))

    posts = full_data.get("posts", [])

    per_post_summary = []
    for idx, p in enumerate(posts, start=1):
        per_post_summary.append(
            {
                "post_id": idx,
                "source": p.get("source", ""),
                "published_at": p.get("published_at", ""),
                "title": p.get("title", ""),
                "url": p.get("url", ""),
                "summary": _short_summary(p.get("excerpt") or p.get("body_text") or ""),
            }
        )

    out = {
        "stage": "final_report",
        "window_days": full_data.get("window_days", 50),
        "total_posts": full_data.get("total_posts", len(posts)),
        "doc_counts": full_data.get("doc_counts", {}),
        "major_keywords": kw_data.get("major_keywords", []),
        "post_summaries": per_post_summary,
    }

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "out_path": str(OUT),
        "total_posts": out["total_posts"],
        "keyword_count": len(out["major_keywords"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
