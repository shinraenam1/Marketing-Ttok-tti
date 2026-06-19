import asyncio
from playwright.async_api import async_playwright

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()
        await page.goto(
            "https://www.samsungcard.com/personal/event/ing/UHPPBE1401M0.jsp",
            wait_until="networkidle", timeout=30000
        )
        await page.wait_for_timeout(2000)

        info = await page.evaluate("""
        () => ({
            allLinks: document.querySelectorAll('a.m_link').length,
            goDtlLinks: document.querySelectorAll("a[onclick*='GoDtlBrws']").length,
            listItems: document.querySelectorAll('.event_list li, .evnt_list li, ul.list li').length,
            moreBtn: (() => {
                for (const el of document.querySelectorAll('a, button')) {
                    const t = el.textContent.trim();
                    if (t === '더보기' || t === '+ 더보기' || t.includes('더보기')) {
                        const s = window.getComputedStyle(el);
                        if (s.display !== 'none') return el.outerHTML.substring(0, 200);
                    }
                }
                return null;
            })(),
            scrollHeight: document.body.scrollHeight,
        })
        """)
        print("Info:", info)

        # Try scrolling and check more events
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)

        after_scroll = await page.evaluate("""
        () => ({
            goDtlLinks: document.querySelectorAll("a[onclick*='GoDtlBrws']").length,
            moreBtn: (() => {
                for (const el of document.querySelectorAll('a, button')) {
                    const t = el.textContent.trim();
                    if (t.includes('더보기')) {
                        const s = window.getComputedStyle(el);
                        if (s.display !== 'none') return el.outerHTML.substring(0, 200);
                    }
                }
                return null;
            })(),
        })
        """)
        print("After scroll:", after_scroll)

        await context.close()
        await browser.close()

asyncio.run(debug())
