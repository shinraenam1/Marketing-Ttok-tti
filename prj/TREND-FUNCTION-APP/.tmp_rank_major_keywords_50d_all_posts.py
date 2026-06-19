import json
from collections import Counter, defaultdict
from pathlib import Path

from src.services.scoring import tokenize

IN_PATH = Path("c:/Users/User/trend-function-app/.tmp_collect_all_50d_full_posts.json")
OUT_PATH = Path("c:/Users/User/trend-function-app/.tmp_major_keywords_50d_all_posts.json")

GENERIC_STOP = {
    "같은", "직접", "아니라", "다른", "어떤", "함께", "바로", "먼저", "것이", "됩니다",
    "어떻게", "새로운", "모든", "좋은", "결국", "가장", "요즘", "지금", "이번", "최근",
    "정리", "모음", "추천", "소개", "보기", "방법", "사람", "사람들", "경우", "관련",
    "중인", "통해", "대해", "대한", "부터", "까지", "처럼", "그리고", "하지만", "또한",
    "있는", "있다", "있어요", "있습니다", "하는", "하며", "해서", "했다", "하면", "되는",
    "에서", "으로", "라는", "입니다", "그냥", "정말", "진짜", "때문", "이런", "저런",
    "wepick", "careet", "gogumafarm",
}

VARIANT_MAP = {
    "ai가": "ai",
    "ai는": "ai",
    "ai의": "ai",
    "브랜드가": "브랜드",
    "브랜드의": "브랜드",
    "제품을": "제품",
    "콘텐츠를": "콘텐츠",
    "실제로": "실제",
}


def normalize_term(term: str) -> str:
    t = (term or "").strip().lower()
    t = VARIANT_MAP.get(t, t)
    return t


def is_usable(term: str) -> bool:
    if not term:
        return False
    if term in GENERIC_STOP:
        return False
    if len(term) < 2:
        return False
    if term.isdigit():
        return False
    if term.endswith(("합니다", "있어요", "입니다", "되는", "하는")):
        return False
    return True


def main() -> None:
    data = json.loads(IN_PATH.read_text(encoding="utf-8"))
    posts = data.get("posts", [])

    keyword_score = Counter()
    keyword_post_map = defaultdict(list)
    keyword_post_seen = defaultdict(set)

    for idx, post in enumerate(posts, start=1):
        title = str(post.get("clean_title") or post.get("title") or "")
        emphasis = str(post.get("clean_emphasis_text") or post.get("emphasis_text") or "")
        body = str(post.get("clean_body_text") or post.get("body_text") or "")

        title_tokens = tokenize(title)
        emphasis_tokens = tokenize(emphasis)
        body_tokens = tokenize(body)

        weighted_terms = Counter()
        for t in body_tokens:
            weighted_terms[normalize_term(t)] += 1.0
        for t in title_tokens:
            weighted_terms[normalize_term(t)] += 1.6
        for t in emphasis_tokens:
            weighted_terms[normalize_term(t)] += 1.9

        for term, score in weighted_terms.items():
            if not is_usable(term):
                continue
            keyword_score[term] += score
            if idx not in keyword_post_seen[term]:
                keyword_post_seen[term].add(idx)
                keyword_post_map[term].append(
                    {
                        "post_id": idx,
                        "source": post.get("source", ""),
                        "published_at": post.get("published_at", ""),
                        "title": post.get("title", ""),
                        "url": post.get("url", ""),
                    }
                )

    ranked = []
    for term, score in keyword_score.items():
        posts_for_term = keyword_post_map[term]
        post_count = len(posts_for_term)
        if post_count < 3:
            continue
        ranked.append(
            {
                "keyword": term,
                "major_score": round(float(score), 4),
                "post_count": post_count,
                "all_related_posts": posts_for_term,
            }
        )

    ranked.sort(key=lambda x: (x["major_score"], x["post_count"]), reverse=True)

    out = {
        "window_days": data.get("window_days"),
        "total_posts": data.get("total_posts", len(posts)),
        "doc_counts": data.get("doc_counts", {}),
        "selection_rule": {
            "min_post_count": 3,
            "generic_stop_filter": True,
            "variant_normalization": True,
        },
        "major_keywords": ranked,
    }

    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    preview = {
        "out_path": str(OUT_PATH),
        "total_posts": out["total_posts"],
        "keyword_count": len(out["major_keywords"]),
        "top10": [
            {
                "keyword": item["keyword"],
                "major_score": item["major_score"],
                "post_count": item["post_count"],
            }
            for item in out["major_keywords"][:10]
        ],
    }
    print(json.dumps(preview, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
