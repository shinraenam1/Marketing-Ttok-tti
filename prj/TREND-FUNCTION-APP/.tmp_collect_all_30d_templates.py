import json
import re
from collections import defaultdict

from src.collectors.web_meme_collectors import WebMemeCollector

LOOKBACK_DAYS = 30
OUT_PATH = "c:/Users/User/trend-function-app/.tmp_collect_all_30d_templates.json"

EXPLICIT_PATTERNS = [
    re.compile(r"나\s*\d{2}년생\s*[^\s,.!?\"'\u201c\u201d]{1,16}인데~?"),
    re.compile(r"[^\n\"'\u201c\u201d]{2,24}인데~"),
    re.compile(r"[^\n\"'\u201c\u201d]{2,24}도\s*해~"),
]
QUOTE_RE = re.compile(r"[\"'\u201c\u201d\u2018\u2019]([^\"'\u201c\u201d\u2018\u2019\n]{4,40})[\"'\u201c\u201d\u2018\u2019]")

NOISE_CONTAINS = {
    "예를 들어",
    "형식의 밈",
    "자기소개",
    "웃음 포인트",
    "브랜드 활용",
    "정리해",
}


def normalize_template(text: str) -> str:
    t = text.strip()
    t = re.sub(r"\s+", " ", t)
    t = t.strip('"\'“”‘’[]()')
    t = re.sub(r"\b\d{2}년생\b", "○○년생", t)
    t = re.sub(r"(○○년생\s+)[^\s,.!?]{1,16}(?=인데)", r"\1○○○", t)
    t = re.sub(r"\b\d+(?:\.?\d+)?\b", "○○", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def is_valid_template(text: str) -> bool:
    if len(text) < 6 or len(text) > 28:
        return False
    if any(noise in text for noise in NOISE_CONTAINS):
        return False
    if text.count(" ") < 1:
        return False
    if not any(k in text for k in ["년생", "인데~", "도 해~", "해~", "챌린지", "밈"]):
        return False
    return True


def extract_templates(text: str):
    hits = []

    for p in EXPLICIT_PATTERNS:
        for m in p.finditer(text):
            hits.append(m.group(0).strip())

    for m in QUOTE_RE.finditer(text):
        phrase = m.group(1).strip()
        if any(k in phrase for k in ["년생", "인데", "해~", "챌린지", "밈"]):
            hits.append(phrase)

    out = []
    seen = set()
    for h in hits:
        n = normalize_template(h)
        if not is_valid_template(n):
            continue
        if n in seen:
            continue
        seen.add(n)
        out.append((n, h))
    return out


def main():
    collector = WebMemeCollector()
    source_docs = collector.collect(max_articles_per_source=None, lookback_days=LOOKBACK_DAYS, include_article_body=True)

    bucket = defaultdict(lambda: {"count": 0, "source_coverage": set(), "examples": []})

    for source, docs in source_docs.items():
        for d in docs:
            text = "\n".join(
                [
                    str(d.get("title", "")),
                    str(d.get("excerpt", "")),
                    str(d.get("body_text", "")),
                    str(d.get("emphasis_text", "")),
                ]
            )

            for norm, raw in extract_templates(text):
                item = bucket[norm]
                item["count"] += 1
                item["source_coverage"].add(source)
                if len(item["examples"]) < 3:
                    item["examples"].append(
                        {
                            "source": source,
                            "title": d.get("title", ""),
                            "url": d.get("url", ""),
                            "raw_match": raw,
                        }
                    )

    ranked = sorted(
        [
            {
                "template": k,
                "count": v["count"],
                "source_coverage": sorted(v["source_coverage"]),
                "examples": v["examples"],
            }
            for k, v in bucket.items()
        ],
        key=lambda x: (x["count"], len(x["source_coverage"]), len(x["template"])),
        reverse=True,
    )

    out = {
        "window_days": LOOKBACK_DAYS,
        "source_health": {
            "wepick": "ok" if source_docs.get("wepick") else "empty",
            "gogumafarm": "ok" if source_docs.get("gogumafarm") else "empty",
            "careet": "ok" if source_docs.get("careet") else "empty",
        },
        "collection_config": {
            "lookback_days": LOOKBACK_DAYS,
            "collect_all_recent": True,
            "max_articles_per_source": None,
        },
        "doc_counts": {k: len(v) for k, v in source_docs.items()},
        "meme_templates": ranked,
        "template_count": len(ranked),
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(json.dumps({
        "window_days": LOOKBACK_DAYS,
        "doc_counts": out["doc_counts"],
        "template_count": out["template_count"],
        "top_templates": out["meme_templates"][:10],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
