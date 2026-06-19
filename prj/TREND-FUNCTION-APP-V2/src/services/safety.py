from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Dict, List, Tuple


def _policy_path() -> str:
    base = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(base, "models", "safety_policy.json")


@lru_cache(maxsize=1)
def load_policy() -> dict:
    default_policy = {
        "version": "fallback-v1",
        "categories": [
            {
                "id": "P0_완전금지",
                "default_action": "block",
                "terms": ["자살", "죽어", "테러", "혐오"],
                "patterns": ["불법\\\\s*(거래|판매|구매)", "(해킹|사기)\\\\s*(방법|가이드)"],
            },
            {
                "id": "P1_강한비속어",
                "default_action": "block",
                "terms": ["ㅅㅂ", "ㅂㅅ", "개새"],
                "patterns": [],
            },
            {
                "id": "P2_브랜드리스크",
                "default_action": "review",
                "terms": ["무조건", "100%", "공짜", "대박보장", "몰빵", "한탕", "패닉", "충격"],
                "patterns": [],
            },
            {
                "id": "P3_주의키워드",
                "default_action": "review",
                "terms": ["가짜", "불안", "중독", "폭망", "논란", "자극", "멘붕"],
                "patterns": [],
            },
        ],
    }

    try:
        with open(_policy_path(), "r", encoding="utf-8") as fp:
            policy = json.load(fp)
        if isinstance(policy, dict) and isinstance(policy.get("categories"), list):
            return policy
    except (OSError, ValueError):
        pass

    return default_policy


def resolve_policy_actions(policy_overrides: dict | None) -> Dict[str, str]:
    actions: Dict[str, str] = {}
    categories = load_policy().get("categories", [])
    for category in categories:
        cat_id = category.get("id")
        default_action = category.get("default_action", "review")
        if isinstance(cat_id, str):
            actions[cat_id] = default_action

    if isinstance(policy_overrides, dict):
        for key, value in policy_overrides.items():
            if key in actions and value in {"block", "review", "ignore"}:
                actions[key] = value

    return actions


def analyze_text_risk(text: str, policy_actions: dict | None = None) -> Dict[str, object]:
    lowered = (text or "").lower()
    categories = load_policy().get("categories", [])
    actions = resolve_policy_actions(policy_actions)

    blocked_terms: List[str] = []
    review_terms: List[str] = []
    risk_flags: List[str] = []

    for category in categories:
        cat_id = category.get("id", "")
        action = actions.get(cat_id, "review")
        if action == "ignore":
            continue

        matched: List[str] = []
        for term in category.get("terms", []):
            if isinstance(term, str) and term.lower() in lowered:
                matched.append(term)

        for pattern in category.get("patterns", []):
            if not isinstance(pattern, str):
                continue
            try:
                compiled = re.compile(pattern)
                if compiled.search(lowered):
                    matched.append(pattern)
            except re.error:
                continue

        if not matched:
            continue

        if action == "block":
            blocked_terms.extend(matched)
        else:
            review_terms.extend(matched)
        risk_flags.append(cat_id)

    blocked_terms = sorted(set(blocked_terms))
    review_terms = sorted(set(review_terms))
    risk_flags = sorted(set(risk_flags))

    risk_score = 0
    risk_score += len(blocked_terms) * 50
    risk_score += len(review_terms) * 15
    risk_score = min(risk_score, 100)

    return {
        "blocked_terms": sorted(set(blocked_terms)),
        "review_terms": sorted(set(review_terms)),
        "risk_flags": risk_flags,
        "risk_score": risk_score,
    }


def safe_copy_suggestion(text: str) -> str:
    candidate = text or ""
    # Replace hard-claim and sensational words first.
    replacements = {
        "무조건": "합리적으로",
        "100%": "높은",
        "공짜": "혜택",
        "대박보장": "추천",
        "몰빵": "집중",
        "한탕": "효율",
        "충격": "주목",
        "패닉": "변화",
        "가짜": "비공식",
        "폭망": "성과 저조",
    }
    for old, new in replacements.items():
        candidate = candidate.replace(old, new)

    # Remove explicit blocked terms when present.
    categories = load_policy().get("categories", [])
    block_terms: List[str] = []
    for category in categories:
        if category.get("default_action") == "block":
            block_terms.extend([t for t in category.get("terms", []) if isinstance(t, str)])
    for term in set(block_terms):
        candidate = candidate.replace(term, "")

    return " ".join(candidate.split())


def evaluate_contents_safety(contents: List[dict], policy_actions: dict | None = None) -> Tuple[List[dict], Dict[str, object]]:
    all_blocked: List[str] = []
    all_flags: List[str] = []
    reviewed_contents: List[dict] = []

    for item in contents:
        text = " ".join([item.get("title", ""), item.get("excerpt", "")])
        risk = analyze_text_risk(text, policy_actions=policy_actions)

        enriched = dict(item)
        enriched["blocked_terms"] = risk["blocked_terms"]
        enriched["risk_flags"] = risk["risk_flags"]
        enriched["risk_score"] = risk["risk_score"]
        reviewed_contents.append(enriched)

        all_blocked.extend(risk["blocked_terms"])
        all_flags.extend(risk["risk_flags"])

    summary = {
        "blocked_terms": sorted(set(all_blocked)),
        "risk_flags": sorted(set(all_flags)),
    }
    return reviewed_contents, summary
