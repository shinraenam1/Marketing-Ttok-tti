"""
Phase 1 디버그 테스트: KB카드 + 페이북 DOM 구조 확인
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def debug_kb_card():
    print("=" * 50)
    print("KB카드 DOM 구조 확인")
    print("=" * 50)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            extra_http_headers={"Accept-Language": "ko-KR,ko;q=0.9"},
            viewport={"width": 1280, "height": 900},
        )
        page = await ctx.new_page()

        # networkidle 로 AJAX 완료까지 대기
        await page.goto(
            "https://card.kbcard.com/BON/DVIEW/HBBMCXCRVNEC0001",
            wait_until="networkidle",
            timeout=30000,
        )
        await page.wait_for_timeout(2000)

        info = await page.evaluate("""
            () => {
                const anchors = document.querySelectorAll('a[onclick*="goDetail"]');
                const first = anchors[0];

                // 다양한 이벤트 관련 셀렉터 시도
                const allLi = document.querySelectorAll('li');
                const lisWithDate = Array.from(allLi).filter(li =>
                    li.textContent.match(/\\d{4}\\.\\d{2}\\.\\d{2}/)
                );

                return {
                    title: document.title,
                    goDetailCount: anchors.length,
                    liTotal: allLi.length,
                    liWithDate: lisWithDate.length,
                    firstOnclick: first ? first.getAttribute('onclick') : null,
                    firstText: first ? first.textContent.trim().substring(0, 100) : null,
                    firstLiWithDate: lisWithDate[0] ? lisWithDate[0].innerHTML.substring(0, 500) : null,
                    // 페이지 소스의 일부 (이벤트 부분)
                    bodySnippet: document.body.innerText.substring(1000, 1500),
                };
            }
        """)
        print(json.dumps(info, ensure_ascii=False, indent=2))
        await browser.close()


async def debug_paybooc():
    print("\n" + "=" * 50)
    print("페이북(BC카드) DOM 구조 확인")
    print("=" * 50)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            extra_http_headers={"Accept-Language": "ko-KR,ko;q=0.9"},
            viewport={"width": 1280, "height": 900},
        )
        page = await ctx.new_page()

        await page.goto(
            "https://web.paybooc.co.kr/web/evnt/main",
            wait_until="networkidle",
            timeout=30000,
        )
        await page.wait_for_timeout(2000)

        info = await page.evaluate("""
            () => {
                // 모든 evnt-dts 링크 (배너 + 리스트)
                const allEvntLinks = document.querySelectorAll('a[href*="evnt-dts"], a[href*="pybcUnifEvntNo"]');
                const first = allEvntLinks[0];

                // 날짜가 있는 li 탐색
                const lisWithDate = Array.from(document.querySelectorAll('li')).filter(li =>
                    li.textContent.match(/\\d{4}\\.\\d{2}\\.\\d{2}/)
                );

                // 이벤트 리스트 컨테이너 탐색
                const listContainers = ['ul.event-list', 'ul.evnt-list', '.event_list ul', 
                    '.evnt_list', '#evntList', '.card-list ul', '.list-wrap ul'];
                let containerFound = null;
                for (const sel of listContainers) {
                    const el = document.querySelector(sel);
                    if (el) { containerFound = {sel, childCount: el.children.length}; break; }
                }

                return {
                    title: document.title,
                    allEvntLinkCount: allEvntLinks.length,
                    totalText: (document.body.innerText.match(/총\\s*\\d+\\s*개/) || ['없음'])[0],
                    lisWithDate: lisWithDate.length,
                    containerFound,
                    firstHref: first ? first.getAttribute('href') : null,
                    // 두 번째, 세 번째 링크 (배너 다음)
                    secondHref: allEvntLinks[1] ? allEvntLinks[1].getAttribute('href') : null,
                    // 날짜가 있는 첫 li의 HTML
                    firstLiHtml: lisWithDate[0] ? lisWithDate[0].innerHTML.substring(0, 500) : null,
                };
            }
        """)
        print(json.dumps(info, ensure_ascii=False, indent=2))
        await browser.close()


async def main():
    await debug_kb_card()
    await debug_paybooc()


if __name__ == "__main__":
    asyncio.run(main())
