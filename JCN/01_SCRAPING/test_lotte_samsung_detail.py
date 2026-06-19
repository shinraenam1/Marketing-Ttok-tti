"""롯데/삼성 상세 페이지 혜택 추출 검증"""
import asyncio
import sys
from playwright.async_api import async_playwright

LOTTE_DETAIL_JS = """
() => {
    const wrap = document.querySelector('.eventDetail');
    if (!wrap) return 'NO .eventDetail';
    const text = wrap.innerText || '';
    const idx = text.indexOf('혜택');
    if (idx >= 0) return text.substring(idx + 2, idx + 400).trim();
    return text.slice(0, 300).trim();
}
"""

SAMSUNG_DETAIL_JS = """
() => {
    const selectors = [
        '.evtDetailCont', '.cont_wrap', '.event-detail-wrap',
        '.event_detail', '#event_detail', '.inner_event', '.sec_event'
    ];
    for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el && el.innerText && el.innerText.length > 50) {
            const text = el.innerText;
            const idx = text.indexOf('혜택');
            if (idx >= 0) return sel + ' => ' + text.substring(idx+2, idx+300).trim();
            return sel + ' => ' + text.slice(0, 200).trim();
        }
    }
    const body = document.body?.innerText || '';
    const idx = body.indexOf('혜택');
    if (idx > 100) return 'BODY => ' + body.substring(idx+2, idx+300).trim();
    return 'NOTHING FOUND title=' + document.title.slice(0,60);
}
"""

TESTS = [
    ("롯데-11171", "https://www.lottecard.co.kr/app/LPBNFDA_V300.lc?evnBultSeq=11171&evnCtgSeq=9999&bigTabGubun=2", "lotte"),
    ("롯데-11172", "https://www.lottecard.co.kr/app/LPBNFDA_V300.lc?evnBultSeq=11172&evnCtgSeq=9999&bigTabGubun=2", "lotte"),
    ("삼성-3748014", "https://www.samsungcard.com/personal/event/ing/UHPPBE1403M0.jsp?cms_id=3748014", "samsung"),
    ("삼성-3748013", "https://www.samsungcard.com/personal/event/ing/UHPPBE1403M0.jsp?cms_id=3748013", "samsung"),
]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124",
            viewport={"width": 1280, "height": 900},
        )
        page = await ctx.new_page()
        for label, url, kind in TESTS:
            print(f"\n[{label}]")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(2000)
                js = LOTTE_DETAIL_JS if kind == "lotte" else SAMSUNG_DETAIL_JS
                result = await page.evaluate(js)
                print(result[:250])
            except Exception as e:
                print(f"ERROR: {e}")
        await browser.close()

asyncio.run(main())
