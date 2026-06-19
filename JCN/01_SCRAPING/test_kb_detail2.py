"""KB 상세 혜택 추출 JS 검증"""
import asyncio
from playwright.async_api import async_playwright

TEST_URLS = [
    ("1001258", "준비! Again2002"),
    ("1001290", "SUMMER PLAY 2026"),
    ("1001279", "여름가전 카드혜택"),
    ("1001276", "트립닷컴 월드컵팩"),
]

KB_DETAIL_JS = """
() => {
    // h3 "내용" 섹션의 다음 형제 요소들 텍스트 추출
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

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for event_id, name in TEST_URLS:
            url = f"https://card.kbcard.com/BON/DVIEW/HBBMCXCRVNEC0001?mainCC=a&eventNum={event_id}"
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(1500)
            raw = await page.evaluate(KB_DETAIL_JS)
            lines = [l.strip() for l in raw.split("\n") if l.strip() and len(l.strip()) > 3]
            print(f"\n[{event_id}] {name}")
            for l in lines[:6]:
                print(f"  {l[:100]}")

        await browser.close()

asyncio.run(main())
