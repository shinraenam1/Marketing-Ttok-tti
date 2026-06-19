"""각 카드사 상세 페이지 DOM 구조 빠른 진단"""
import asyncio
from playwright.async_api import async_playwright

SAMPLES = {
    "KB국민카드":  "https://card.kbcard.com/BON/DVIEW/HBBMCXCRVNEC0002?evtNo=1001290",
    "페이북":      "https://web.paybooc.co.kr/web/evnt/evnt-dts?pybcUnifEvntNo=2026060026",
    "롯데카드":    "https://www.lottecard.co.kr/app/LPBNFDB_V100.lc?evntNo=11172",
    "삼성카드":    "https://www.samsungcard.com/personal/event/ing/UHPPBE0202M0.jsp?evtId=3748014",
}

PROBE_JS = """
() => {
    const hints = [];

    // 텍스트 밀도 높은 요소 탐색
    const candidates = Array.from(document.querySelectorAll(
        'section, article, div, ul, p'
    ));
    candidates.forEach(el => {
        const t = (el.innerText || '').trim();
        if (t.length < 80 || t.length > 5000) return;
        // 수치 포함 여부 체크
        const hasNum = /\\d+\\s*(%|원|배|회|포인트|캐시백|할인|적립)/.test(t);
        if (!hasNum) return;

        const cls = (el.className || '').substring(0, 60);
        const id  = (el.id || '').substring(0, 30);
        hints.push({ sel: el.tagName.toLowerCase() + (id ? '#'+id : '') + (cls ? '.'+cls.split(' ').join('.') : ''), len: t.length, preview: t.substring(0, 120) });
    });

    // 밀도 순 정렬 후 상위 5개
    hints.sort((a,b) => b.len - a.len);
    return hints.slice(0, 5);
}
"""

async def probe(company, url, page):
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2000)
        results = await page.evaluate(PROBE_JS)
        print(f"\n=== {company} ===")
        for r in results:
            print(f"  [{r['sel'][:60]}] len={r['len']}")
            print(f"    {r['preview'][:100]}")
    except Exception as e:
        print(f"=== {company} === ERROR: {e}")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        for company, url in SAMPLES.items():
            page = await ctx.new_page()
            await probe(company, url, page)
            await page.close()
        await ctx.close()
        await browser.close()

asyncio.run(main())
