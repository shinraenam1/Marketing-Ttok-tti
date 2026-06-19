"""
Phase 1 실제 수집 테스트: KB국민카드 + 페이북(BC카드)
"""
import asyncio
import json
import os
from scrapers.kb_card import scrape_kb_card
from scrapers.paybooc import scrape_paybooc


async def main():
    os.makedirs("output", exist_ok=True)

    print("\n" + "=" * 56)
    print("  Phase 1 – KB국민카드 & 페이북(BC카드) 스크래핑 테스트")
    print("=" * 56)

    # ── KB국민카드
    print("\n[1/2] KB국민카드 이벤트 수집 중...")
    try:
        kb = await scrape_kb_card()
        print(f"\n  ✓ KB국민카드: {len(kb)}건 수집")
        if kb:
            print("  첫 번째 이벤트 샘플:")
            print(json.dumps(kb[0], ensure_ascii=False, indent=4))
        with open("output/kb_card_test.json", "w", encoding="utf-8") as f:
            json.dump(kb, f, ensure_ascii=False, indent=2)
        print(f"  → output/kb_card_test.json 저장")
    except Exception as e:
        print(f"  ✗ 오류: {type(e).__name__}: {e}")
        kb = []

    # ── 페이북(BC카드)
    print("\n[2/2] 페이북(BC카드) 이벤트 수집 중...")
    try:
        pb = await scrape_paybooc()
        print(f"\n  ✓ 페이북(BC카드): {len(pb)}건 수집")
        if pb:
            print("  첫 번째 이벤트 샘플:")
            print(json.dumps(pb[0], ensure_ascii=False, indent=4))
        with open("output/paybooc_test.json", "w", encoding="utf-8") as f:
            json.dump(pb, f, ensure_ascii=False, indent=2)
        print(f"  → output/paybooc_test.json 저장")
    except Exception as e:
        print(f"  ✗ 오류: {type(e).__name__}: {e}")
        pb = []

    print("\n" + "=" * 56)
    print("Phase 1 결과")
    print(f"  KB국민카드    : {len(kb)}건")
    print(f"  페이북(BC카드): {len(pb)}건")
    print("=" * 56)


if __name__ == "__main__":
    asyncio.run(main())
