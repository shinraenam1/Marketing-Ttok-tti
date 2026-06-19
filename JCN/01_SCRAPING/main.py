"""
카드사 이벤트 수집 메인 실행 파일
Phase 1 : KB국민카드 + 페이북(BC카드)  ← 2개 테스트
Phase 2 : 롯데카드 + 삼성카드          ← 전체 수집 (Lazy Loading 포함)
"""

import asyncio
import json
import os
from datetime import datetime

from scrapers.kb_card import scrape_kb_card
from scrapers.paybooc import scrape_paybooc
from scrapers.lotte_card import scrape_lotte_card
from scrapers.samsung_card import scrape_samsung_card

OUTPUT_DIR = "output"


def save_json(data: list, filename: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  → 저장 완료: {filepath}  ({len(data)}건)")
    return filepath


async def run_scraper(name: str, func):
    """단일 스크래퍼 실행 및 오류 처리"""
    try:
        events = await func()
        print(f"  ✓ {name}: {len(events)}건 수집")
        return events
    except Exception as e:
        print(f"  ✗ {name} 오류: {type(e).__name__}: {e}")
        return []


async def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    all_results: dict[str, list] = {}

    # ────────────────────────────────────────────────────────
    # Phase 1 – KB국민카드 & 페이북(BC카드) 테스트
    # ────────────────────────────────────────────────────────
    print("\n" + "=" * 62)
    print("  Phase 1 — KB국민카드 & 페이북(BC카드) 스크래핑 테스트")
    print("=" * 62)

    print("\n[1/4] KB국민카드 이벤트 수집 중…")
    kb_events = await run_scraper("KB국민카드", scrape_kb_card)
    all_results["KB국민카드"] = kb_events
    if kb_events:
        save_json(kb_events, f"kb_card_{ts}.json")

    print("\n[2/4] 페이북(BC카드) 이벤트 수집 중…")
    paybooc_events = await run_scraper("페이북(BC카드)", scrape_paybooc)
    all_results["페이북(BC카드)"] = paybooc_events
    if paybooc_events:
        save_json(paybooc_events, f"paybooc_{ts}.json")

    print("\n─── Phase 1 결과 ─────────────────────────────────────")
    print(f"  KB국민카드    : {len(all_results['KB국민카드'])}건")
    print(f"  페이북(BC카드): {len(all_results['페이북(BC카드)'])}건")
    print("─────────────────────────────────────────────────────\n")

    # ────────────────────────────────────────────────────────
    # Phase 2 – 롯데카드 & 삼성카드 (Lazy Loading / 페이징 포함)
    # ────────────────────────────────────────────────────────
    print("=" * 62)
    print("  Phase 2 — 롯데카드 & 삼성카드 전체 수집")
    print("=" * 62)

    print("\n[3/4] 롯데카드 이벤트 수집 중…")
    lotte_events = await run_scraper("롯데카드", scrape_lotte_card)
    all_results["롯데카드"] = lotte_events
    if lotte_events:
        save_json(lotte_events, f"lotte_card_{ts}.json")

    print("\n[4/4] 삼성카드 이벤트 수집 중…")
    samsung_events = await run_scraper("삼성카드", scrape_samsung_card)
    all_results["삼성카드"] = samsung_events
    if samsung_events:
        save_json(samsung_events, f"samsung_card_{ts}.json")

    # ────────────────────────────────────────────────────────
    # 전체 통합 JSON 저장
    # ────────────────────────────────────────────────────────
    combined = [
        {
            "card_company": company,
            "count": len(events),
            "scraped_at": datetime.now().isoformat(),
            "events": events,
        }
        for company, events in all_results.items()
    ]
    save_json(combined, f"all_card_events_{ts}.json")

    # 최종 요약
    total = sum(len(v) for v in all_results.values())
    print("\n" + "=" * 62)
    print("  스크래핑 완료 요약")
    print("=" * 62)
    for company, events in all_results.items():
        print(f"  {company:<15}: {len(events):>3}건")
    print(f"  {'합계':<15}: {total:>3}건")
    print("=" * 62)


if __name__ == "__main__":
    asyncio.run(main())
