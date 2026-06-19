import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

IN_PATH = Path("c:/Users/User/trend-function-app/.tmp_final_report_50d.json")
OUT_PATH = Path("c:/Users/User/trend-function-app/.tmp_trending_memes_from_final_50d.json")

TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣]{2,20}")

MEME_CUES = {
    "밈", "챌린지", "릴스", "숏폼", "유행", "트렌드", "밈키피디아",
    "말랑이", "엄미새", "백룸", "야호", "회전샷", "포맷", "깡",
}

NOISE = {
    "브랜드", "콘텐츠", "마케팅", "검색", "광고", "전략", "요즘", "이번", "최근",
    "가이드", "정리", "방법", "사람", "사람들", "고객", "제품",
}


def parse_dt(v: str):
    s = str(v or "").strip()
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def tokenize(text: str):
    out = []
    for t in TOKEN_RE.findall((text or "").lower()):
        if len(t) < 2:
            continue
        if t in NOISE:
            continue
        if t.isdigit():
            continue
        out.append(t)
    return out


def main():
    data = json.loads(IN_PATH.read_text(encoding="utf-8"))
    posts = data.get("post_summaries", [])

    term_tf = Counter()
    term_df = Counter()
    term_last_seen = {}
    term_posts = defaultdict(list)

    now = datetime.now(timezone.utc)

    for p in posts:
        title = str(p.get("title", ""))
        dt = parse_dt(p.get("published_at")) or now
        toks = tokenize(title)

        # build simple phrase candidates from title tokens
        phrases = []
        for i in range(len(toks) - 1):
            phrases.append(f"{toks[i]} {toks[i+1]}")

        candidates = set(toks)
        for ph in phrases:
            if any(cue in ph for cue in MEME_CUES):
                candidates.add(ph)

        # promote explicit meme cue terms from title
        for cue in MEME_CUES:
            if cue in title.lower():
                candidates.add(cue)

        seen_local = set()
        for c in candidates:
            if c in NOISE:
                continue
            if len(c) < 2:
                continue

            base = 1.0
            if any(cue in c for cue in MEME_CUES):
                base += 1.8
            if " " in c:
                base += 0.4

            term_tf[c] += base
            if c not in seen_local:
                term_df[c] += 1
                seen_local.add(c)

            prev = term_last_seen.get(c)
            if prev is None or dt > prev:
                term_last_seen[c] = dt

            if len(term_posts[c]) < 4:
                term_posts[c].append(
                    {
                        "title": title,
                        "url": p.get("url", ""),
                        "source": p.get("source", ""),
                        "published_at": p.get("published_at", ""),
                    }
                )

    if not term_tf:
        out = {
            "window_days": data.get("window_days"),
            "total_posts": data.get("total_posts"),
            "trending_memes": [],
        }
        OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"trending_memes": 0, "out_path": str(OUT_PATH)}, ensure_ascii=False, indent=2))
        return

    max_tf = max(term_tf.values())
    max_df = max(term_df.values())

    ranked = []
    for term, tf in term_tf.items():
        df = term_df[term]
        if df < 2 and not any(cue in term for cue in MEME_CUES):
            continue

        tf_score = tf / max_tf
        df_score = df / max_df

        last_seen = term_last_seen.get(term, now)
        hours = max((now - last_seen).total_seconds() / 3600.0, 1.0)
        recency = 1.0 / (1.0 + (hours / (24.0 * 7.0)))

        cue_bonus = 0.25 if any(cue in term for cue in MEME_CUES) else 0.0

        trend_score = (0.45 * tf_score + 0.30 * df_score + 0.25 * recency + cue_bonus) * 100.0

        ranked.append(
            {
                "meme": term,
                "trend_score": round(trend_score, 2),
                "post_count": int(df),
                "last_seen_at": last_seen.isoformat(),
                "samples": term_posts[term],
            }
        )

    ranked.sort(key=lambda x: (x["trend_score"], x["post_count"]), reverse=True)

    out = {
        "window_days": data.get("window_days"),
        "total_posts": data.get("total_posts"),
        "source_breakdown": data.get("doc_counts", {}),
        "trending_memes": ranked[:40],
    }

    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "out_path": str(OUT_PATH),
                "trending_memes_top10": out["trending_memes"][:10],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
