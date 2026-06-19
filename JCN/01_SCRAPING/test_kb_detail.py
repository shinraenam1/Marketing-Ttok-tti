"""KB 상세 페이지 DOM 구조 탐색"""
import asyncio
from playwright.async_api import async_playwright

TEST_URLS = [
    "https://card.kbcard.com/BON/DVIEW/HBBMCXCRVNEC0001?mainCC=a&eventNum=1001258",
    "https://card.kbcard.com/BON/DVIEW/HBBMCXCRVNEC0001?mainCC=a&eventNum=1001290",
]

PROBE_JS = """
() => {
    const results = {};

    // 1) 후보 컨테이너들
    const candidates = [
        '#evt_detail', '.evtDetailCont', '.event-detail-wrap',
        '.evt-detail', '.detail-content', '.content-area',
        'article', 'main', '.event_cont', '.event-cont',
        '[class*="evtDetail"]', '[class*="event_detail"]',
    ];
    results.containers = candidates.map(sel => {
        const el = document.querySelector(sel);
        return el ? sel + ' ✅ (len=' + el.innerText.length + ')' : sel + ' ✗';
    });

    // 2) h3 목록
    results.h3s = Array.from(document.querySelectorAll('h3')).map(h => h.textContent.trim());

    // 3) h4 목록
    results.h4s = Array.from(document.querySelectorAll('h4')).map(h => h.textContent.trim());

    // 4) dt 목록
    results.dts = Array.from(document.querySelectorAll('dt')).map(d => d.textContent.trim());

    // 5) "내용" 텍스트 포함 요소 찾기
    const allEls = Array.from(document.querySelectorAll('*'));
    const naeyongEls = allEls.filter(el =>
        el.children.length === 0 && el.textContent.trim() === '내용'
    );
    results.naeyong_tags = naeyongEls.map(el => el.tagName + '.' + el.className + ' parent=' + el.parentElement?.className);

    // 6) 페이지 title
    results.page_title = document.title;

    // 7) 전체 텍스트 상위 300자
    const body = document.body?.innerText || '';
    const idx = body.indexOf('내용');
    if (idx >= 0) {
        results.around_naeyong = body.substring(Math.max(0, idx - 50), idx + 200);
    }

    return results;
}
"""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for url in TEST_URLS:
            print(f"\n{'='*60}")
            print(f"URL: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2000)

            result = await page.evaluate(PROBE_JS)
            print("페이지 제목:", result.get("page_title"))
            print("\n[컨테이너]")
            for c in result.get("containers", []):
                if "✅" in c:
                    print(" ", c)
            print("\n[h3 태그]", result.get("h3s"))
            print("[h4 태그]", result.get("h4s"))
            print("[dt 태그]", result.get("dts"))
            print("\n['내용' 요소]", result.get("naeyong_tags"))
            print("\n['내용' 주변 텍스트]:")
            print(result.get("around_naeyong", "(없음)"))

        await browser.close()

asyncio.run(main())
