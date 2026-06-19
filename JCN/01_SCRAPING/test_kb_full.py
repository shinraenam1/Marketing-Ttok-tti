"""KB국민카드만 스크래핑 + 상세 혜택 추출 전체 테스트"""
import asyncio
import json
import os
import re
import sys
from datetime import datetime
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.dirname(__file__))
from scrapers.kb_card import scrape_kb_card as kb_scrape

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
CONCURRENCY = 5
DETAIL_TIMEOUT = 18000

NUM_RE = re.compile(r"[\d,]+\s*(%|원|배|회|포인트|캐시백|할인|적립|쿠폰|천원|만원|달러|마일)")

def best_benefit_line(lines: list[str]) -> str:
    scored = []
    for line in lines:
        line = line.strip()
        if len(line) < 6 or len(line) > 250:
            continue
        if any(x in line for x in ["Copyright", "©", "로그인", "회원가입", "전체메뉴", "홈으로", "구분\t"]):
            continue
        nc = len(NUM_RE.findall(line))
        bc = sum(1 for k in ["할인", "적립", "혜택", "지급", "증정", "무이자", "캐시백"] if k in line)
        if nc + bc > 0:
            scored.append((nc * 3 + bc * 2, line))
    scored.sort(reverse=True)
    if scored:
        return scored[0][1][:200]
    for line in lines:
        line = line.strip()
        if len(line) >= 10 and not any(x in line for x in ["©", "로그인", "전체메뉴"]):
            return line[:150]
    return ""

KB_DETAIL_JS = """
() => {
    const h3s = Array.from(document.querySelectorAll('h3'));
    const naeyong = h3s.find(h => h.textContent.trim() === '내용');
    if (!naeyong) return '';

    const parts = [];
    let el = naeyong.nextElementSibling;
    let count = 0;
    while (el && el.tagName !== 'H3' && count < 8) {
        const text = el.innerText ? el.innerText.trim() : el.textContent.trim();
        if (text && text.length > 3) parts.push(text);
        el = el.nextElementSibling;
        count++;
    }
    return parts.join('\\n');
}
"""

async def fetch_kb_detail(page, url: str) -> str:
    await page.goto(url, wait_until="domcontentloaded", timeout=DETAIL_TIMEOUT)
    await page.wait_for_timeout(1500)
    raw = await page.evaluate(KB_DETAIL_JS)
    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    return best_benefit_line(lines)

async def process_one(sem, context, event: dict, idx: int, total: int) -> dict:
    async with sem:
        url = event.get("url", "")
        page = await context.new_page()
        try:
            summary = await fetch_kb_detail(page, url)
            if not summary:
                summary = event.get("title", "")
            event["benefit_summary"] = summary
            print(f"  [{idx+1:3}/{total}] {event['title'][:35]:35s} | {summary[:60]}")
        except Exception as e:
            event["benefit_summary"] = event.get("title", "")
            print(f"  [{idx+1:3}/{total}] ❌ {event['title'][:35]:35s} | {str(e)[:50]}")
        finally:
            await page.close()
        return event

async def main():
    print("━━━ KB국민카드 이벤트 수집 ━━━")
    kb_events = await kb_scrape()
    print(f"수집 완료: {len(kb_events)}건")

    # 수집된 URL 샘플 확인
    for e in kb_events[:3]:
        print(f"  URL 확인: {e['url']}")

    print(f"\n━━━ 상세 혜택 스크래핑 ({len(kb_events)}건) ━━━")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        sem = asyncio.Semaphore(CONCURRENCY)
        tasks = [
            process_one(sem, context, e, i, len(kb_events))
            for i, e in enumerate(kb_events)
        ]
        results = await asyncio.gather(*tasks)
        await browser.close()

    # 결과 저장
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUTPUT_DIR, f"kb_detailed_{ts}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 저장: {os.path.basename(out_path)} ({len(results)}건)")
    print("\n[결과 샘플]")
    for e in results[:10]:
        print(f"  {e['title'][:40]:40s} → {e['benefit_summary'][:70]}")

asyncio.run(main())
