import json
from collections import defaultdict
from pathlib import Path

IN_PATH = Path("c:/Users/User/trend-function-app/.tmp_collect_all_50d_processed.json")
OUT_PATH = Path("c:/Users/User/trend-function-app/.tmp_major_keywords_50d.json")

GENERIC_STOP = {
    "같은", "직접", "아니라", "다른", "어떤", "함께", "바로", "먼저", "것이", "됩니다",
    "어떻게", "새로운", "모든", "좋은", "결국", "가장", "요즘", "지금", "이번", "최근",
    "정리", "모음", "추천", "소개", "보기", "방법", "사람", "사람들", "경우", "관련",
    "중인", "통해", "대해", "대한", "부터", "까지", "처럼", "그리고", "하지만", "또한",
    "있는", "있다", "있어요", "있습니다", "하는", "하며", "해서", "했다", "하면", "되는",
    "에서", "으로", "라는", "입니다", "그냥", "정말", "진짜", "때문", "이런", "저런",
    "브랜드", "콘텐츠", "트렌드", "유행", "고구마팜", "careet", "wepick",
}

CUE_TERMS = {
    "밈", "챌린지", "릴스", "숏폼", "굿즈", "소비", "경제", "ai", "환각", "검색", "aeo",
    "gwp", "스카프", "트윌리", "콜라보", "팬덤", "런칭", "캠페인", "인용", "자막", "캡션",
    "말랑이", "엄미새", "z세대",
}


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

    term_stats = defaultdict(lambda: {"score": 0.0, "post_count": 0, "sample_titles": []})

    for post in posts:
        seen = set()
        title = str(post.get("title", ""))
        terms = post.get("duplicate_weighted_terms", [])
        for item in terms:
            term = str(item.get("term", "")).strip().lower()
            if not is_usable(term):
                continue

            score = float(item.get("duplicate_weight", 0.0))
            if term in CUE_TERMS:
                score *= 1.25

            term_stats[term]["score"] += score
            if term not in seen:
                term_stats[term]["post_count"] += 1
                seen.add(term)
            if len(term_stats[term]["sample_titles"]) < 3 and title:
                term_stats[term]["sample_titles"].append(title)

    ranked = sorted(
        (
            {
                "keyword": t,
                "major_score": round(v["score"], 4),
                "post_count": int(v["post_count"]),
                "sample_titles": v["sample_titles"],
            }
            for t, v in term_stats.items()
            if v["post_count"] >= 3
        ),
        key=lambda x: (x["major_score"], x["post_count"]),
        reverse=True,
    )

    out = {
        "window_days": data.get("window_days"),
        "total_posts": data.get("total_posts"),
        "selection_rule": {
            "min_post_count": 3,
            "generic_stop_filter": True,
            "cue_boost": 1.25,
        },
        "major_keywords": ranked[:30],
    }

    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "out_path": str(OUT_PATH),
        "major_keywords_top10": out["major_keywords"][:10],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
