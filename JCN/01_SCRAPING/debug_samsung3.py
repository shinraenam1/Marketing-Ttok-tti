import asyncio
from playwright.async_api import async_playwright

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        
        all_requests = []
        async def on_request(req):
            all_requests.append(req.url)
        
        page = await context.new_page()
        page.on("request", on_request)
        await page.goto(
            "https://www.samsungcard.com/personal/event/ing/UHPPBE1401M0.jsp",
            wait_until="networkidle", timeout=30000
        )
        await page.wait_for_timeout(2000)

        # Get all event IDs
        event_ids = await page.evaluate("""
        () => Array.from(document.querySelectorAll("a[onclick*='GoDtlBrws']"))
            .map(a => {
                const m = a.getAttribute('onclick').match(/GoDtlBrws\\s*\\(\\s*'([^']+)'/);
                return m ? m[1] : null;
            }).filter(Boolean)
        """)
        print(f"Total events: {len(event_ids)}")
        print("Event IDs:", event_ids)

        # Find relevant requests (XHR/fetch for event data)
        relevant = [u for u in all_requests if 'event' in u.lower() or 'evnt' in u.lower() or 'evnt' in u.lower()]
        print(f"\nEvent-related requests ({len(relevant)}):")
        for u in relevant[:15]:
            print(" ", u)

        await context.close()
        await browser.close()

asyncio.run(debug())
