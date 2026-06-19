"""
KB국민카드 이벤트 스크래퍼
URL  : https://card.kbcard.com/BON/DVIEW/HBBMCXCRVNEC0001
방식 : doSearchSpider("HBBMCXCRVNEC0001", pageNum) JS 함수 호출로 페이지 전환
"""

from playwright.async_api import async_playwright, Page

LIST_URL = "https://card.kbcard.com/BON/DVIEW/HBBMCXCRVNEC0001"
BASE_URL = "https://card.kbcard.com"

# ─── JS: 현재 페이지의 이벤트 목록 추출 ───────────────────────────────────────
_EXTRACT_JS = """
() => {
    const now = new Date().toISOString();
    const results = [];

    // href 속성에 goDetail 포함된 앵커 탐색 (onclick이 아닌 href 사용!)
    const anchors = Array.from(document.querySelectorAll('a[href*="goDetail"]'));
    if (anchors.length === 0) return results;

    anchors.forEach(anchor => {
        // ── 이벤트 ID / URL ──────────────────────────────────────────────────
        const href = anchor.getAttribute('href') || '';
        const idMatch = href.match(/goDetail\\s*\\(\\s*['"]([\\w]+)['"]/);
        const eventId = idMatch ? idMatch[1] : '';
        const url = eventId
            ? `https://card.kbcard.com/BON/DVIEW/HBBMCXCRVNEC0001?mainCC=a&eventNum=${eventId}`
            : '';

        // ── 제목 (.evtlist-desc .subject) ───────────────────────────────────
        const subjectEl = anchor.querySelector('.evtlist-desc .subject, .subject');
        let title = subjectEl
            ? subjectEl.textContent.trim().replace(/\\s+/g, ' ')
            : anchor.textContent.trim().replace(/\\s+/g, ' ')
                .replace(/\\d{4}\\.\\d{2}\\.\\d{2}.*$/, '').trim();

        // ── 날짜 (.evtlist-desc .date) ──────────────────────────────────────
        const dateEl = anchor.querySelector('.evtlist-desc .date, .date');
        let dateRange = dateEl ? dateEl.textContent.trim() : '';
        if (!dateRange) {
            const dm = (anchor.textContent || '').match(
                /(\\d{4}\\.\\d{2}\\.\\d{2})[~\\-](\\d{4}\\.\\d{2}\\.\\d{2})/
            );
            if (dm) dateRange = dm[0];
        }

        // ── 카테고리 (.evtlist-desc .category em) ───────────────────────────
        const categoryEms = anchor.querySelectorAll('.evtlist-desc .category em, .category em');
        const categories = Array.from(categoryEms)
            .map(em => em.textContent.trim())
            .filter(Boolean);

        // ── 썸네일 (span.thumb img) ──────────────────────────────────────────
        const img = anchor.querySelector('span.thumb img, .thumb img, img');
        let thumbnail = img ? (img.getAttribute('src') || '') : '';
        if (thumbnail && thumbnail.startsWith('//')) thumbnail = 'https:' + thumbnail;
        if (thumbnail && thumbnail.startsWith('/'))  thumbnail = 'https://card.kbcard.com' + thumbnail;

        // ── 날짜 파싱 ─────────────────────────────────────────────────────────
        const dm2 = dateRange.match(/(\\d{4}\\.\\d{2}\\.\\d{2})[~\\-](\\d{4}\\.\\d{2}\\.\\d{2})/);

        if (eventId || title) {
            results.push({
                card_company: 'KB국민카드',
                event_id: eventId,
                title,
                subtitle: '',
                date_range: dateRange,
                start_date: dm2 ? dm2[1] : '',
                end_date:   dm2 ? dm2[2] : '',
                categories,
                like_count: 0,
                thumbnail,
                url,
                scraped_at: now,
            });
        }
    });

    return results;
}
"""

# ─── JS: 다음 페이지로 이동 ──────────────────────────────────────────────────
# 페이지 링크: <a href="javascript:doSearchSpider(&quot;HBBMCXCRVNEC0001&quot;,&quot;2&quot;)">2</a>
# (getAttribute('href') 호출 시 &quot; → " 자동 디코딩됨)
_NEXT_PAGE_JS = """
(nextPage) => {
    // href 속성에 doSearchSpider 포함된 링크 탐색
    const links = Array.from(document.querySelectorAll('a[href*="doSearchSpider"]'));
    for (const link of links) {
        const href = link.getAttribute('href') || '';
        // 예: javascript:doSearchSpider("HBBMCXCRVNEC0001","2")
        const m = href.match(/"(\\d+)"\\s*\\)/);
        if (m && parseInt(m[1]) === nextPage) {
            link.click();
            return 'page';
        }
    }

    // 현재 페이지 그룹의 '다음 그룹' 버튼 탐색 (예: 1-10 다음 → 11-20)
    for (const link of links) {
        const txt = (link.textContent || '').trim();
        const title = (link.getAttribute('title') || '').trim();
        if (txt.includes('다음') || title.includes('다음')) {
            link.click();
            return 'group';
        }
    }

    return null;
}
"""


async def _parse_page(page: Page) -> list[dict]:
    return await page.evaluate(_EXTRACT_JS)


async def scrape_kb_card() -> list[dict]:
    """KB국민카드 진행 이벤트 전체 수집 (페이지 이동 포함)"""
    all_events: list[dict] = []
    seen_ids: set[str] = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
            extra_http_headers={"Accept-Language": "ko-KR,ko;q=0.9"},
        )
        page = await context.new_page()

        print(f"    접속: {LIST_URL}")
        await page.goto(LIST_URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        page_num = 1
        consecutive_empty = 0

        while True:
            print(f"    [{page_num}페이지] 파싱 중…", end=" ")
            events = await _parse_page(page)

            added = 0
            for e in events:
                uid = e.get("event_id") or (e["title"] + e.get("start_date", ""))
                if uid and uid not in seen_ids:
                    all_events.append(e)
                    seen_ids.add(uid)
                    added += 1

            print(f"{added}건 신규 / 누계 {len(all_events)}건")

            if added == 0:
                consecutive_empty += 1
                if consecutive_empty >= 2:
                    print("    연속 2회 신규 없음 → 종료")
                    break
            else:
                consecutive_empty = 0

            # 다음 페이지 이동 시도
            next_page = page_num + 1
            moved = await page.evaluate(_NEXT_PAGE_JS, next_page)
            if not moved:
                print("    다음 페이지 버튼 없음 → 종료")
                break

            await page.wait_for_timeout(2500)
            page_num = next_page

        await context.close()
        await browser.close()

    return all_events
