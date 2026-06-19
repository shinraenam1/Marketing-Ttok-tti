"""
Phase 3 디버그: Paybooc 이벤트 데이터 속성 + 롯데/삼성카드 구조 확인
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def debug_paybooc_attrs():
    print("=" * 55)
    print("Paybooc - 이벤트 li 데이터 속성 + 날짜 확인")
    print("=" * 55)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 Windows AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
            extra_http_headers={"Accept-Language": "ko-KR,ko;q=0.9"},
            viewport={"width": 1280, "height": 900},
        )
        page = await ctx.new_page()
        await page.goto("https://web.paybooc.co.kr/web/evnt/main", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        info = await page.evaluate("""
            () => {
                const items = document.querySelectorAll('ul.event-list li');
                const first = items[0];
                if (!first) return {error: 'no items'};

                // 모든 data 속성 확인
                const dataAttrs = {};
                Array.from(first.attributes).forEach(a => {
                    dataAttrs[a.name] = a.value;
                });

                // anchor의 모든 속성
                const anchor = first.querySelector('a');
                const anchorAttrs = {};
                if (anchor) {
                    Array.from(anchor.attributes).forEach(a => {
                        anchorAttrs[a.name] = a.value;
                    });
                }

                // 전체 li innerHTML (길게)
                const fullHtml = first.innerHTML;

                // img src에서 이벤트 번호 추출 시도
                const img = first.querySelector('img');
                const imgSrc = img ? img.getAttribute('src') : '';
                const evtNumMatch = imgSrc.match(/(\\d{10})_main/);

                return {
                    firstLiDataAttrs: dataAttrs,
                    firstAnchorAttrs: anchorAttrs,
                    imgSrc,
                    evtNumFromImg: evtNumMatch ? evtNumMatch[1] : null,
                    fullHtml: fullHtml.substring(0, 1200),
                    // 날짜 패턴 탐색
                    hasDateText: /\\d{4}\\.\\d{2}\\.\\d{2}/.test(fullHtml),
                    allText: first.textContent.trim().replace(/\\s+/g, ' ').substring(0, 200),
                };
            }
        """)
        print(json.dumps(info, ensure_ascii=False, indent=2))
        await browser.close()


async def debug_lotte():
    print("\n" + "=" * 55)
    print("롯데카드 이벤트 리스트 구조 확인")
    print("=" * 55)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 Windows AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
            extra_http_headers={"Accept-Language": "ko-KR,ko;q=0.9"},
            viewport={"width": 1280, "height": 900},
        )
        page = await ctx.new_page()
        await page.goto("https://www.lottecard.co.kr/app/LPBNFDA_V100.lc", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        info = await page.evaluate("""
            () => {
                // 다양한 이벤트 리스트 탐색
                const selectors = ['#evntList li', '.evnt_list li', '.event_list li',
                    '.board_list li', '.evtList li', '.lst_event li'];
                let items = [], usedSel = '';
                for (const sel of selectors) {
                    items = document.querySelectorAll(sel);
                    if (items.length > 0) { usedSel = sel; break; }
                }

                // 날짜 패턴이 있는 모든 li
                const lisWithDate = Array.from(document.querySelectorAll('li')).filter(li =>
                    li.textContent.match(/\\d{4}\\.\\d{2}\\.\\d{2}/)
                );

                // 더보기 버튼 탐색
                const moreBtns = [];
                document.querySelectorAll('a, button').forEach(el => {
                    const txt = el.textContent.trim();
                    if (txt === '더보기' || txt.startsWith('더보기')) {
                        moreBtns.push({tag: el.tagName, class: el.className, href: el.getAttribute('href')});
                    }
                });

                // 현재/전체 카운트 텍스트
                const countText = document.body.innerText.match(/(\\d+)\\s*\\/\\s*(\\d+)/);

                return {
                    usedSelector: usedSel,
                    itemCount: items.length,
                    lisWithDate: lisWithDate.length,
                    moreBtns,
                    countText: countText ? countText[0] : null,
                    firstLiWithDateHtml: lisWithDate[0] ? lisWithDate[0].innerHTML.substring(0, 600) : null,
                    allText: document.body.innerText.substring(1500, 2200),
                };
            }
        """)
        print(json.dumps(info, ensure_ascii=False, indent=2))
        await browser.close()


async def debug_samsung():
    print("\n" + "=" * 55)
    print("삼성카드 이벤트 리스트 구조 확인")
    print("=" * 55)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 Windows AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
            extra_http_headers={"Accept-Language": "ko-KR,ko;q=0.9"},
            viewport={"width": 1280, "height": 900},
        )
        page = await ctx.new_page()
        await page.goto(
            "https://www.samsungcard.com/personal/event/ing/UHPPBE1401M0.jsp",
            wait_until="networkidle",
            timeout=30000,
        )
        await page.wait_for_timeout(2000)

        info = await page.evaluate("""
            () => {
                const selectors = ['.event_list > li', '.evtList > li', '#eventList > li',
                    '.list_event > li', 'ul[class*="event"] > li', 'ul[class*="list"] > li'];
                let items = [], usedSel = '';
                for (const sel of selectors) {
                    items = document.querySelectorAll(sel);
                    if (items.length > 0) { usedSel = sel; break; }
                }

                // 날짜 패턴 li
                const lisWithDate = Array.from(document.querySelectorAll('li')).filter(li =>
                    li.textContent.match(/\\d{4}\\.\\d{2}\\.\\d{2}/)
                );

                // 페이지네이션 탐색
                const pagingEl = document.querySelector('.paging, .pagination, [class*="page_nav"]');

                const first = lisWithDate[0];
                return {
                    title: document.title,
                    usedSelector: usedSel,
                    itemCount: items.length,
                    lisWithDate: lisWithDate.length,
                    firstLiHtml: first ? first.innerHTML.substring(0, 700) : null,
                    pagingHtml: pagingEl ? pagingEl.outerHTML.substring(0, 500) : null,
                };
            }
        """)
        print(json.dumps(info, ensure_ascii=False, indent=2))
        await browser.close()


async def main():
    await debug_paybooc_attrs()
    await debug_lotte()
    await debug_samsung()


if __name__ == "__main__":
    asyncio.run(main())
