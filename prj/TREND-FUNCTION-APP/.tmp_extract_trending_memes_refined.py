import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

IN_PATH = Path("c:/Users/User/trend-function-app/.tmp_collect_all_50d_full_posts.json")
OUT_PATH = Path("c:/Users/User/trend-function-app/.tmp_trending_memes_refined_50d.json")

TITLE_TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣]{2,24}")
YEAR_BORN_RE = re.compile(r"나\s*\d{2}년생\s*[^\s,.!?]{1,16}인데~?")
QUOTE_RE = re.compile(r"[\"'“”‘’]([^\"'“”‘’\n]{3,40})[\"'“”‘’]")

CUES = {
    "밈", "챌린지", "릴스", "숏폼", "유행", "트렌드", "포맷", "회전샷",
    "말랑이", "엄미새", "백룸", "니가 좋아", "그린 그린", "야호",
}

BLOCK = {
    "고구마팜", "wepick", "careet", "브랜드", "마케팅", "광고", "검색", "콘텐츠",
    "이유", "방법", "가이드", "정리", "소개", "이번", "요즘", "최근", "공식",
}


def norm(s: str) -> str:
    t = " ".join((s or "").split()).strip().lower()
    t = t.strip("'\"“”‘’[]()")
    t = re.sub(r"\d{2}년생", "○○년생", t)
    t = re.sub(r"(○○년생\s+)[^\s,.!?]{1,16}(?=인데)", r"\1○○○", t)
    return t


def parse_dt(v: str):
    s = str(v or "").strip()
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def extract_candidates(title: str, body: str, emphasis: str):
    out = set()
    t = title or ""
    b = body or ""
    e = emphasis or ""

    # Explicit meme template.
    for m in YEAR_BORN_RE.finditer("\n".join([t, b, e])):
        out.add(norm(m.group(0)))

    # Quoted meme-like expressions.
    for m in QUOTE_RE.finditer("\n".join([t, b[:1200], e])):
        q = norm(m.group(1))
        if any(cue in q for cue in CUES) or ("인데~" in q):
            out.add(q)

    # Cue terms and cue phrases from title tokens.
    tokens = [tok.lower() for tok in TITLE_TOKEN_RE.findall(t)]
    for tok in tokens:
        if tok in BLOCK:
            continue
        if tok in CUES:
            out.add(tok)

    for i in range(len(tokens) - 1):
        ph = norm(tokens[i] + " " + tokens[i + 1])
        if any(cue in ph for cue in CUES):
            out.add(ph)

    # Keep known hot meme markers if present in text.
    joined = (t + "\n" + b[:2000] + "\n" + e).lower()
    for marker in ["나 ○○년생", "엄미새", "말랑이", "백룸", "챌린지", "회전샷", "릴스"]:
        if marker in joined:
            out.add(norm(marker))

    clean = set()
    for c in out:
        if not c or len(c) < 2:
            continue
        if c in BLOCK:
            continue
        if c.isdigit():
            continue
        clean.add(c)
    return clean


def main():
    data = json.loads(IN_PATH.read_text(encoding="utf-8"))
    posts = data.get("posts", [])
    now = datetime.now(timezone.utc)

    tf = Counter()
    df = Counter()
    last_seen = {}
    samples = defaultdict(list)

    for p in posts:
        title = str(p.get("title", ""))
        body = str(p.get("body_text", ""))
        emphasis = str(p.get("emphasis_text", ""))
        dt = parse_dt(p.get("published_at")) or now

        cands = extract_candidates(title, body, emphasis)
        seen = set()
        for c in cands:
            boost = 1.0
            if any(cue in c for cue in CUES):
                boost += 1.5
            if "○○년생" in c:
                boost += 1.2
            tf[c] += boost
            if c not in seen:
                df[c] += 1
                seen.add(c)
            if len(samples[c]) < 4:
                samples[c].append(
                    {
                        "title": title,
                        "url": p.get("url", ""),
                        "source": p.get("source", ""),
                        "published_at": p.get("published_at", ""),
                    }
                )
            if c not in last_seen or dt > last_seen[c]:
                last_seen[c] = dt

    max_tf = max(tf.values()) if tf else 1.0
    max_df = max(df.values()) if df else 1.0

    ranked = []
    for meme, v in tf.items():
        d = df[meme]
        # For cue memes allow single appearance; otherwise require at least 2.
        if d < 2 and not any(cue in meme for cue in CUES) and "○○년생" not in meme:
            continue

        tf_score = v / max_tf
        df_score = d / max_df
        hrs = max((now - last_seen.get(meme, now)).total_seconds() / 3600.0, 1.0)
        recency = 1.0 / (1.0 + hrs / (24.0 * 10.0))

        score = (0.45 * tf_score + 0.35 * df_score + 0.20 * recency) * 100.0

        ranked.append(
            {
                "meme": meme,
                "trend_score": round(score, 2),
                "post_count": int(d),
                "last_seen_at": last_seen.get(meme, now).isoformat(),
                "samples": samples[meme],
            }
        )

    ranked.sort(key=lambda x: (x["trend_score"], x["post_count"]), reverse=True)

    out = {
        "window_days": data.get("window_days", 50),
        "total_posts": data.get("total_posts", len(posts)),
        "doc_counts": data.get("doc_counts", {}),
        "trending_memes": ranked[:25],
    }

    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out_path": str(OUT_PATH), "top10": out["trending_memes"][:10]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
