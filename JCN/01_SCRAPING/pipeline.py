"""
파이프라인 래퍼 – function_app.py 에서 POST /api/scrape 가 호출하는 모듈.
run_pipeline() 은 4개 카드사 수집 → 상세 스크래핑 → JSON 저장 후
{ total, file, by_category } 딕셔너리를 반환합니다.
"""

import asyncio
import glob
import json
import os
from datetime import datetime

from playwright.async_api import async_playwright

from scrapers.kb_card     import scrape_kb_card
from scrapers.paybooc     import scrape_paybooc
from scrapers.lotte_card  import scrape_lotte_card
from scrapers.samsung_card import scrape_samsung_card
from scrape_details import (
    process_one,
    categorize,
    benefit_from_title,
    CONCURRENCY,
)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


async def _collect_all() -> list[dict]:
    """4개 카드사 이벤트 목록 수집"""
    async def run(name, func):
        try:
            return await func()
        except Exception as e:
            print(f"[pipeline] {name} 수집 오류: {e}")
            return []

    # Phase 1 – KB + 페이북 (병렬)
    kb_ev, pb_ev = await asyncio.gather(
        run("KB국민카드", scrape_kb_card),
        run("페이북(BC카드)", scrape_paybooc),
    )

    # Phase 2 – 롯데 + 삼성 (병렬)
    lt_ev, ss_ev = await asyncio.gather(
        run("롯데카드", scrape_lotte_card),
        run("삼성카드", scrape_samsung_card),
    )

    return kb_ev + pb_ev + lt_ev + ss_ev


async def _enrich_details(events: list[dict]) -> list[dict]:
    """Playwright 로 상세 페이지 스크래핑 → benefit_summary / category_new 추가"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
            extra_http_headers={"Accept-Language": "ko-KR,ko;q=0.9"},
        )
        sem = asyncio.Semaphore(CONCURRENCY)
        tasks = [
            process_one(sem, context, e, i, len(events))
            for i, e in enumerate(events)
        ]
        results = await asyncio.gather(*tasks)
        await browser.close()
    return list(results)


def _save(events: list[dict]) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(OUTPUT_DIR, f"events_detailed_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    return path


async def run_pipeline() -> dict:
    """
    전체 파이프라인 실행.
    반환값:
      {
        "total": 249,
        "file": "output/events_detailed_20260619_165022.json",
        "by_category": [{"category": "여행", "count": 93}, ...]
      }
    """
    print("[pipeline] 1단계: 이벤트 목록 수집")
    events = await _collect_all()
    print(f"[pipeline] 수집 완료: {len(events)}건")

    print("[pipeline] 2단계: 상세 혜택 스크래핑")
    events = await _enrich_details(events)

    print("[pipeline] 3단계: JSON 저장")
    filepath = _save(events)
    print(f"[pipeline] 저장 완료: {filepath}")

    # 카테고리 집계
    cat_counts: dict[str, int] = {}
    for e in events:
        cat = e.get("category_new", "기타")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    by_category = sorted(
        [{"category": k, "count": v} for k, v in cat_counts.items()],
        key=lambda x: x["count"], reverse=True,
    )

    return {
        "total":       len(events),
        "file":        filepath,
        "by_category": by_category,
    }
