"""롯데/삼성 상세 페이지 body 텍스트 직접 확인"""
import asyncio
from playwright.async_api import async_playwright

SAMPLES = {
    "롯데카드":    "https://www.lottecard.co.kr/app/LPBNFDB_V100.lc?evntNo=11172",
    "삼성카드":    "https://www.samsungcard.com/personal/event/ing/UHPPBE0202M0.jsp?evtId=3748014",
}

async def probe(company, url, page):
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2000)

        info = await page.evaluate("""
        () => {
            // 네비 제거
            ['header','footer','nav','.gnb','.lnb','.header','.footer',
             'script','style','.breadcrumb'].forEach(s => {
                document.querySelectorAll(s).forEach(e => e.remove());
            });
            // body text first 1500 chars
            const body = document.body.innerText.trim();

            // find divs/sections with most text
            const els = Array.from(document.querySelectorAll('div, section, article, ul'));
            const top = els
                .filter(e => {
                    const t = (e.innerText||'').trim();
                    return t.length > 50 && t.length < 3000;
                })
                .sort((a,b) => b.innerText.length - a.innerText.length)
                .slice(0,3)
                .map(e => ({
                    sel: (e.tagName + (e.id?'#'+e.id:'') + (e.className?' .'+e.className.split(' ').slice(0,2).join('.'):'') ).substring(0,60),
                    text: e.innerText.trim().substring(0, 300)
                }));

            return { body: body.substring(0, 800), top };
        }
        """)
        print(f"\n=== {company} ===")
        print(f"BODY FIRST 800:\n{info['body']}")
        print("\nTOP ELEMENTS:")
        for t in info['top']:
            print(f"  [{t['sel']}]")
            print(f"    {t['text'][:200]}")
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
