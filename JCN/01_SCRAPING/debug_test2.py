"""
Phase 2 디버그: KB카드 페이지네이션 + Paybooc 리스트 아이템 구조 확인
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def debug_kb_pagination():
    print("=" * 50)
    print("KB카드 페이지네이션 구조 확인")
    print("=" * 50)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
            extra_http_headers={"Accept-Language": "ko-KR,ko;q=0.9"},
            viewport={"width": 1280, "height": 900},
        )
        page = await ctx.new_page()
        await page.goto("https://card.kbcard.com/BON/DVIEW/HBBMCXCRVNEC0001", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        info = await page.evaluate("""
            () => {
                // href 기반 goDetail 링크 확인
                const hrefAnchors = document.querySelectorAll('a[href*="goDetail"]');
                
                // doSearchSpider 링크 확인 (href vs onclick)
                const hrefPaging = document.querySelectorAll('a[href*="doSearchSpider"]');
                const onclickPaging = document.querySelectorAll('a[onclick*="doSearchSpider"]');
                
                // 페이지네이션 영역 HTML
                const pagingEl = document.querySelector('.paging, .pagination, #pagingBox, [class*="page"]');
                
                return {
                    hrefGoDetailCount: hrefAnchors.length,
                    hrefDoSearchSpiderCount: hrefPaging.length,
                    onclickDoSearchSpiderCount: onclickPaging.length,
                    firstGoDetailHref: hrefAnchors[0] ? hrefAnchors[0].getAttribute('href') : null,
                    pagingHtml: pagingEl ? pagingEl.outerHTML.substring(0, 600) : null,
                    // 첫 이벤트 전체 li HTML
                    firstEventLi: (() => {
                        const lisWithDate = Array.from(document.querySelectorAll('li')).filter(li =>
                            li.textContent.match(/\\d{4}\\.\\d{2}\\.\\d{2}/) && li.querySelector('a[href*="goDetail"]')
                        );
                        return lisWithDate[0] ? lisWithDate[0].innerHTML.substring(0, 600) : null;
                    })(),
                };
            }
        """)
        print(json.dumps(info, ensure_ascii=False, indent=2))
        await browser.close()


async def debug_paybooc_list():
    print("\n" + "=" * 50)
    print("페이북 이벤트 리스트 아이템 구조 확인")
    print("=" * 50)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
            extra_http_headers={"Accept-Language": "ko-KR,ko;q=0.9"},
            viewport={"width": 1280, "height": 900},
        )
        page = await ctx.new_page()
        await page.goto("https://web.paybooc.co.kr/web/evnt/main", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        info = await page.evaluate("""
            () => {
                // ul.event-list li 구조
                const listItems = document.querySelectorAll('ul.event-list li');
                const first = listItems[0];
                const second = listItems[1];
                
                return {
                    itemCount: listItems.length,
                    firstItemHtml: first ? first.innerHTML.substring(0, 800) : null,
                    secondItemHtml: second ? second.innerHTML.substring(0, 800) : null,
                };
            }
        """)
        print(json.dumps(info, ensure_ascii=False, indent=2))
        await browser.close()


async def main():
    await debug_kb_pagination()
    await debug_paybooc_list()


if __name__ == "__main__":
    asyncio.run(main())
