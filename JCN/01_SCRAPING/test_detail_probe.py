"""롯데/삼성/페이북 상세 페이지 DOM 탐색"""
import asyncio
from playwright.async_api import async_playwright

PROBE_JS = """
() => {
    const h = (tag) => Array.from(document.querySelectorAll(tag)).map(e => e.textContent.trim().slice(0,80)).filter(Boolean).slice(0,5);
    const body = document.body?.innerText || '';
    // 핵심 섹션 텍스트 (첫 600자)
    const idx = Math.min(
        body.indexOf('혜택') >= 0 ? body.indexOf('혜택') : 9999,
        body.indexOf('할인') >= 0 ? body.indexOf('할인') : 9999,
        body.indexOf('적립') >= 0 ? body.indexOf('적립') : 9999
    );
    return {
        title: document.title,
        h2: h('h2'), h3: h('h3'), h4: h('h4'),
        benefit_area: body.substring(Math.max(0, idx-30), idx+500),
        candidates: [
            '.benefit-area', '.evt-content', '.event-detail',
            '.eventDetail', '.bx_event_view', '.view_cont',
            '.evtDetailCont', '#content', 'article', 'main',
            '[class*=benefit]', '[class*=detail]', '[id*=content]'
        ].map(sel => {
            const el = document.querySelector(sel);
            return el ? `${sel} ✅ len=${el.innerText.length}` : `${sel} ✗`;
        }).filter(s => s.includes('✅'))
    };
}
"""

URLS = [
    ("롯데-리스트", "https://www.lottecard.co.kr/app/LPBNFDA_V100.lc"),
    ("롯데-상세V300", "https://www.lottecard.co.kr/app/LPBNFDA_V300.lc?evnBultSeq=11171&evnCtgSeq=9999&bigTabGubun=2"),
    ("롯데-상세V300b", "https://www.lottecard.co.kr/app/LPBNFDA_V300.lc?evnBultSeq=11172&evnCtgSeq=9999&bigTabGubun=2"),
    ("삼성-상세1403", "https://www.samsungcard.com/personal/event/ing/UHPPBE1403M0.jsp?cms_id=3748014"),
    ("페이북-상세", "https://web.paybooc.co.kr/web/evnt/evnt-dts?pybcUnifEvntNo=2026060026&evntMrktTypCd=&ordering=RECENT&ingPositionTop=500"),
]

async def probe(page, label, url):
    print(f"\n{'='*55}")
    print(f"[{label}] {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=25000)
        await page.wait_for_timeout(2500)
        r = await page.evaluate(PROBE_JS)
        print("제목:", r["title"][:60])
        print("컨테이너:", r["candidates"][:4] if r["candidates"] else "없음")
        print("h2:", r["h2"][:3])
        print("h3:", r["h3"][:3])
        print("혜택 주변 텍스트:")
        print(r["benefit_area"][:300])
    except Exception as e:
        print("ERROR", str(e)[:100])

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124",
            viewport={"width": 1280, "height": 900},
        )
        page = await ctx.new_page()
        for label, url in URLS:
            await probe(page, label, url)
        await browser.close()

asyncio.run(main())
