from __future__ import annotations

from typing import List


CARD_SYNONYMS = {
    "card discount": ["billing discount", "instant discount", "cashback", "benefit"],
    "korean_card_discount": ["cheonggu discount", "immediate discount", "cashback", "event"],
    "card": ["credit card", "card event", "card benefit"],
    "cardsale": ["discount", "benefit", "promotion"],
    "carddiscount": ["billing discount", "cashback", "promotion"],
    "cardhalin": ["billing discount", "cashback", "promotion"],
}


def normalize_keyword(keyword: str) -> str:
    text = (keyword or "").strip().lower()
    if not text:
        return ""
    return text.replace("  ", " ")


def expand_keyword(keyword: str) -> List[str]:
    normalized = normalize_keyword(keyword)
    expanded = [keyword.strip()] if keyword.strip() else []

    if "card" in normalized or "\uce74\ub4dc" in keyword:
        expanded.extend(["card discount", "billing discount", "instant discount", "cashback", "card benefit"])

    for key, values in CARD_SYNONYMS.items():
        if key in normalized:
            expanded.extend(values)

    unique = []
    seen = set()
    for item in expanded:
        item_norm = normalize_keyword(item)
        if not item_norm or item_norm in seen:
            continue
        seen.add(item_norm)
        unique.append(item)
    return unique
