import asyncio
from playwright.async_api import async_playwright

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )

        # Capture XHR/API requests
        api_calls = []
        async def on_response(resp):
            ct = resp.headers.get("content-type", "")
            if resp.status == 200 and ("json" in ct or "javascript" in ct):
                api_calls.append(resp.url)

        page = await context.new_page()
        page.on("response", on_response)
        await page.goto(
            "https://www.samsungcard.com/personal/event/ing/UHPPBE1401M0.jsp",
            wait_until="networkidle", timeout=30000
        )
        await page.wait_for_timeout(2000)

        # Pagination HTML
        paging_html = await page.evaluate("""
        () => {
            const sels = ['.paging', '.pagination', '[class*="paging"]', '[class*="page"]'];
            for (const s of sels) {
                const el = document.querySelector(s);
                if (el) return el.outerHTML.substring(0, 600);
            }
            return null;
        }
        """)
        print("=== Paging HTML ===")
        print(paging_html)

        # Event count
        cnt = await page.evaluate("""
        () => document.querySelectorAll('a.m_link[onclick*="GoDtlBrws"]').length
        """)
        print(f"\nEvents on page: {cnt}")

        # Check total count text in page
        total_text = await page.evaluate("""
        () => {
            const m = document.body.innerText.match(/총\\s*[\\d,]+\\s*[개건]/);
            return m ? m[0] : '';
        }
        """)
        print(f"Total count text: {total_text}")

        # Look for all onclick page buttons
        page_btns = await page.evaluate("""
        () => {
            const btns = Array.from(document.querySelectorAll('a[onclick*="page"], button[onclick*="page"], a[href*="page"]'));
            return btns.slice(0, 10).map(b => ({
                tag: b.tagName, text: b.textContent.trim().substring(0, 30),
                onclick: (b.getAttribute('onclick') || '').substring(0, 80),
                href: (b.getAttribute('href') || '').substring(0, 80)
            }));
        }
        """)
        print(f"\nPage buttons: {page_btns}")

        # API calls summary
        print(f"\nAPI calls captured ({len(api_calls)}):")
        for u in api_calls[:10]:
            print(" ", u[:120])

        # Try clicking page 2
        print("\n--- Trying to navigate to page 2 ---")
        clicked = await page.evaluate("""
        () => {
            // Find page 2 button
            for (const el of document.querySelectorAll('a, button')) {
                const txt = el.textContent.trim();
                if (txt === '2') {
                    const s = window.getComputedStyle(el);
                    if (s.display !== 'none') {
                        el.click();
                        return el.outerHTML.substring(0, 200);
                    }
                }
            }
            return null;
        }
        """)
        print(f"Page 2 click result: {clicked}")

        if clicked:
            await page.wait_for_timeout(3000)
            cnt2 = await page.evaluate("""
            () => document.querySelectorAll('a.m_link[onclick*="GoDtlBrws"]').length
            """)
            print(f"Events after nav to page 2: {cnt2}")
            # Get current URL
            print(f"Current URL: {page.url}")
            # Get first event ID on page 2
            first_id = await page.evaluate("""
            () => {
                const a = document.querySelector('a.m_link[onclick*="GoDtlBrws"]');
                if (!a) return null;
                const m = a.getAttribute('onclick').match(/GoDtlBrws\\s*\\(\\s*'([^']+)'/);
                return m ? m[1] : null;
            }
            """)
            print(f"First event ID on page 2: {first_id}")

        await context.close()
        await browser.close()

asyncio.run(debug())
