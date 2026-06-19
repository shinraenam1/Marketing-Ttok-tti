from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Tuple

TOKEN_RE = re.compile(r"[0-9A-Za-z\uac00-\ud7a3]{2,12}")
TITLE_TOKEN_RE = re.compile(r"[0-9A-Za-z\uac00-\ud7a3]{1,20}")
STOPWORDS = {
    "https",
    "www",
    "com",
    "video",
    "event",
    "benefit",
    "discount",
    "card",
    "the",
    "this",
    "with",
    "from",
    "that",
    "you",
    "your",
    "about",
}

KO_STOPWORDS = {
    "있어요",
    "있습니다",
    "있는",
    "있다",
    "가장",
    "요즘",
    "지금",
    "이것",
    "그것",
    "저것",
    "우리",
    "여기",
    "저기",
    "정리",
    "총정리",
    "모음",
    "추천",
    "콘텐츠",
    "소개",
    "보기",
    "방법",
    "사람",
    "사람들",
    "경우",
    "관련",
    "중인",
    "통해",
    "대해",
    "대한",
    "부터",
    "까지",
    "처럼",
    "에서",
    "으로",
    "에서의",
    "그리고",
    "하지만",
    "또한",
    "이번",
    "최근",
    "최신",
    "라는",
    "이용",
    "위해",
    "통한",
    "하고",
    "하는",
    "하는데",
    "되는",
    "읽는",
    "빠른",
    "만드는",
    "북마크",
    "모았습니다",
    "확인",
    "보세요",
    "유행중",
    "유행",
    "지금챙겨야",
}

LOW_SIGNAL_SUFFIXES = (
    "하는",
    "했다",
    "합니다",
    "하며",
    "하여",
    "에서",
    "으로",
    "에게",
    "까지",
)

GENERIC_SINGLE_TERMS = {
    "글로벌",
    "핫한",
    "국내외",
    "레퍼런스",
    "크리에이터",
    "브랜드",
    "콘텐츠",
    "트렌드",
    "유행",
    "북마크",
}

TREND_CUE_TERMS = {
    "밈",
    "챌린지",
    "샷",
    "포맷",
    "굿즈",
    "릴스",
    "소비",
    "경제",
}

PROPER_NOUN_CUE_SUFFIXES = (
    "밈",
    "챌린지",
    "샷",
    "포맷",
    "경제",
)

PHRASE_NOISE_TOKENS = {
    "함께",
    "읽으면",
    "읽어야",
    "보여드릴까요",
    "콘텐츠를",
    "찾는다고",
    "합니다",
    "있어요",
    "하는",
    "하면",
    "되는",
    "그리고",
}


def tokenize(text: str) -> List[str]:
    tokens = TOKEN_RE.findall((text or "").lower())
    return [
        t
        for t in tokens
        if t not in STOPWORDS
        and t not in KO_STOPWORDS
        and not t.isdigit()
        and not t.startswith("http")
        and len(t) >= 2
        and not any(t.endswith(sfx) for sfx in LOW_SIGNAL_SUFFIXES)
    ]


def extract_phrase_candidates(text: str) -> List[str]:
    tokens = tokenize(text)
    if not tokens:
        return []

    candidates: List[str] = []
    candidates.extend(tokens)

    for i in range(len(tokens) - 1):
        candidates.append(f"{tokens[i]} {tokens[i+1]}")

    for i in range(len(tokens) - 2):
        candidates.append(f"{tokens[i]} {tokens[i+1]} {tokens[i+2]}")

    return candidates


def extract_proper_noun_candidates(raw_title: str) -> List[str]:
    text = (raw_title or "").strip()
    if not text:
        return []

    results: List[str] = []

    # 1) Quoted expressions are often the meme phrase itself.
    quote_pattern = r"[\"'\u201c\u2018\[]([^\]" + "\u201d\u2019" + r"]{2,30})[\"\u201d\u2019\]]"
    for m in re.finditer(quote_pattern, text):
        phrase = m.group(1).strip().lower()
        phrase_tokens = [t for t in tokenize(phrase) if t not in GENERIC_SINGLE_TERMS]
        if len(phrase_tokens) >= 1:
            results.append(" ".join(phrase_tokens[:3]))

    # 2) Capture 1-2 tokens before cue suffix words, e.g. "거제 야호 밈".
    raw_tokens = TITLE_TOKEN_RE.findall(text)
    lower_tokens = [t.lower() for t in raw_tokens]
    for idx, token in enumerate(lower_tokens):
        if token in PROPER_NOUN_CUE_SUFFIXES:
            start = max(0, idx - 2)
            candidate_tokens = [t for t in lower_tokens[start:idx] if t and t not in KO_STOPWORDS]
            if candidate_tokens:
                phrase = " ".join(candidate_tokens)
                if phrase not in GENERIC_SINGLE_TERMS:
                    results.append(phrase)

    unique: List[str] = []
    seen = set()
    for item in results:
        norm = " ".join(item.split())
        if not norm or norm in seen:
            continue
        seen.add(norm)
        unique.append(norm)
    return unique


def extract_meme_candidates(documents: Iterable[dict], top_k: int = 20) -> List[dict]:
    weighted_term_counts: Dict[str, float] = defaultdict(float)
    term_doc_counts: Counter = Counter()
    term_sources: Dict[str, set] = defaultdict(set)
    term_last_seen: Dict[str, datetime] = {}
    term_proper_hits: Counter = Counter()
    term_emphasis_hits: Counter = Counter()
    document_count = 0

    for doc in documents:
        document_count += 1
        # Title + emphasis text captures the explicit phrase cues editors intentionally highlight.
        title_text = str(doc.get("clean_title") or doc.get("title", ""))
        emphasis_text = str(doc.get("clean_emphasis_text") or doc.get("emphasis_text", ""))
        source = doc.get("source", "unknown")
        terms = extract_phrase_candidates(title_text)
        emphasis_terms = extract_phrase_candidates(emphasis_text)
        proper_terms = extract_proper_noun_candidates(str(doc.get("title", "")))
        terms.extend(proper_terms)
        unique_terms = set(terms).union(set(emphasis_terms))
        # Use document-level frequency to avoid long-body repetition dominating rankings.
        term_doc_counts.update(unique_terms)

        for term in set(terms):
            weighted_term_counts[term] += 1.0
        for term in set(proper_terms):
            weighted_term_counts[term] += 0.6
        for term in set(emphasis_terms):
            weighted_term_counts[term] += 0.7

        for term in unique_terms:
            term_sources[term].add(source)
        for term in set(proper_terms):
            term_proper_hits[term] += 1
        for term in set(emphasis_terms):
            term_emphasis_hits[term] += 1

        last_seen_raw = doc.get("published_at")
        try:
            last_seen = datetime.fromisoformat(str(last_seen_raw).replace("Z", "+00:00"))
        except ValueError:
            last_seen = datetime.now(timezone.utc)

        for term in unique_terms:
            prev = term_last_seen.get(term)
            if prev is None or last_seen > prev:
                term_last_seen[term] = last_seen

    max_freq = max(weighted_term_counts.values()) if weighted_term_counts else 1.0
    now = datetime.now(timezone.utc)

    scored = []
    for term, freq in weighted_term_counts.items():
        term_tokens = term.split()
        is_phrase = len(term_tokens) >= 2
        doc_freq = float(term_doc_counts.get(term, 0))

        min_doc_freq = 1.0 if is_phrase else 2.0
        if doc_freq < min_doc_freq:
            continue

        if not is_phrase and term in GENERIC_SINGLE_TERMS:
            continue

        if not is_phrase and len(term) <= 2:
            continue

        if is_phrase:
            if any(tok in PHRASE_NOISE_TOKENS for tok in term_tokens):
                continue
            if any(tok.endswith(("요", "다", "까", "면", "야")) for tok in term_tokens):
                continue

        if doc_freq == 1.0:
            if not any(cue in term for cue in TREND_CUE_TERMS):
                continue

        doc_ratio = (doc_freq / float(document_count)) if document_count > 0 else 0.0
        source_span = len(term_sources[term])
        recency_hours = max((now - term_last_seen.get(term, now)).total_seconds() / 3600.0, 1.0)
        recency = 1.0 / math.log2(recency_hours + 2.0)

        freq_score = freq / max_freq
        spread_score = min(source_span / 3.0, 1.0)
        growth_score = min((freq / 5.0), 1.0)
        recency_score = min(recency, 1.0)
        yt_boost = 1.0 if "youtube" in term_sources[term] else 0.0
        ubiquity_penalty = max(0.0, min(1.0, (doc_ratio - 0.6) / 0.4))
        phrase_bonus = 0.12 if is_phrase else 0.0
        cue_bonus = 0.08 if any(cue in term for cue in TREND_CUE_TERMS) else 0.0
        proper_bonus = 0.15 if term_proper_hits.get(term, 0) > 0 else 0.0
        emphasis_bonus = min(0.12, 0.04 * float(term_emphasis_hits.get(term, 0)))

        meme_score = (
            0.28 * freq_score
            + 0.22 * spread_score
            + 0.22 * growth_score
            + 0.18 * recency_score
            + 0.10 * yt_boost
            + phrase_bonus
            + cue_bonus
            + proper_bonus
            + emphasis_bonus
            - 0.18 * ubiquity_penalty
        ) * 100.0

        stage = "emerging"
        if meme_score >= 80:
            stage = "hot"
        elif meme_score >= 60:
            stage = "stable"
        elif meme_score < 35:
            stage = "fading"

        scored.append(
            {
                "keyword": term,
                "meme_score": round(meme_score, 2),
                "stage": stage,
                "growth_rate_pct": round(growth_score * 100.0, 2),
                "source_coverage": sorted(term_sources[term]),
                "last_seen_at": term_last_seen.get(term, now).isoformat(),
            }
        )

    scored.sort(key=lambda x: x["meme_score"], reverse=True)
    return scored[:top_k]


def lexical_overlap_score(text: str, keywords: List[str]) -> float:
    text_tokens = set(tokenize(text))
    if not keywords:
        return 0.0

    kw_tokens = set()
    for kw in keywords:
        kw_tokens.update(tokenize(kw))

    if not kw_tokens:
        return 0.0

    matched = len(text_tokens.intersection(kw_tokens))
    return matched / len(kw_tokens)


def score_related_content(contents: List[dict], expanded_keywords: List[str]) -> List[dict]:
    scored: List[dict] = []

    for item in contents:
        text = " ".join(
            [
                str(item.get("clean_title") or item.get("title", "")),
                str(item.get("clean_excerpt") or item.get("excerpt", "")),
                str(item.get("clean_emphasis_text") or item.get("emphasis_text", "")),
            ]
        )
        lexical = lexical_overlap_score(text, expanded_keywords)
        semantic = lexical
        co_occurrence = min(1.0, lexical * 1.2)
        relevance = (0.45 * lexical + 0.35 * semantic + 0.20 * co_occurrence) * 100.0

        views = float(item.get("stats", {}).get("views", 0))
        comments = float(item.get("stats", {}).get("comments", 0))
        engagement = min(1.0, (views / 100000.0) + (comments / 2000.0)) * 100.0

        content_score = 0.35 * relevance + 0.35 * relevance + 0.20 * engagement + 0.10 * 80.0

        matched_terms = [k for k in expanded_keywords if any(t in text.lower() for t in tokenize(k))]

        enriched = dict(item)
        enriched["matched_terms"] = matched_terms
        enriched["relevance_score"] = round(relevance, 2)
        enriched["content_score"] = round(content_score, 2)
        scored.append(enriched)

    scored.sort(key=lambda x: x["content_score"], reverse=True)
    return scored
