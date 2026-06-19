"""
페이북(BC카드) 이벤트 스크래퍼
URL  : https://web.paybooc.co.kr/web/evnt/main
방식 : 56개 이벤트가 ul.event-list에 전부 로드됨 (별도 페이징 없음)

실제 DOM 구조 (디버그로 확인):
  <ul class="event-list">
    <li class="event-item" data-cate="03"
        onclick="moveDetailIngPage(2026060026, null, 'RECENT')">
      <a href="#link" class="event-link">
        <div class="event-img-wrap"><img src="...2026060026_main.png"></div>
        <div class="event-name">
          <p class="event-sub-tit">제주신화월드</p>
          <p class="event-tit">객실 5% 할인<br>테마파크 26% 할인</p>
        </div>
      </a>
    </li>
  </ul>
  → 이벤트 번호: li.onclick에서 moveDetailIngPage(ID, ...) 추출
  → 날짜: 리스트 뷰에 없음 (detail 페이지에만 존재)
"""

from playwright.async_api import async_playwright, Page

LIST_URL = "https://web.paybooc.co.kr/web/evnt/main"
BASE_URL = "https://web.paybooc.co.kr"

# 카테고리 코드 → 한글 매핑
CATE_MAP = {
    "01": "생활편의",
    "02": "카드혜택",
    "03": "여행/해외",
    "04": "자동차/렌탈",
    "05": "문화/공연",
    "06": "정기결제",
    "07": "금융/무이자",
    "08": "쇼핑",
    "09": "골프",
}

# ─── JS: 이벤트 목록 추출 ────────────────────────────────────────────────────
_EXTRACT_JS = """
() => {
    const now = new Date().toISOString();
    const results = [];
    const BASE = 'https://web.paybooc.co.kr';

    // ul.event-list li.event-item 탐색
    const items = Array.from(document.querySelectorAll('ul.event-list li.event-item, ul.event-list li'));
    if (items.length === 0) return results;

    items.forEach(item => {
        // ── 이벤트 번호 (li.onclick에서 추출) ────────────────────────────────
        const onclick = item.getAttribute('onclick') || '';
        const idMatch = onclick.match(/moveDetailIngPage\\s*\\(\\s*(\\d+)/);
        const eventId = idMatch ? idMatch[1] : '';
        const url = eventId
            ? `${BASE}/web/evnt/evnt-dts?pybcUnifEvntNo=${eventId}`
            : '';

        // ── 카테고리 (data-cate 속성) ────────────────────────────────────────
        const cateCode = item.getAttribute('data-cate') || '';
        const cateMap = {
            '01':'생활편의','02':'카드혜택','03':'여행/해외',
            '04':'자동차/렌탈','05':'문화/공연','06':'정기결제',
            '07':'금융/무이자','08':'쇼핑','09':'골프'
        };
        const categories = cateCode ? [cateMap[cateCode] || cateCode] : [];

        // ── 제목 (.event-name .event-tit) ────────────────────────────────────
        const titEl = item.querySelector('.event-name .event-tit, .event-tit');
        const title = titEl ? titEl.textContent.trim().replace(/\\s+/g, ' ') : '';

        // ── 부제목 (.event-name .event-sub-tit) ──────────────────────────────
        const subEl = item.querySelector('.event-name .event-sub-tit, .event-sub-tit');
        const subtitle = subEl ? subEl.textContent.trim().replace(/\\s+/g, ' ') : '';

        // ── 썸네일 (.event-img-wrap img) ─────────────────────────────────────
        const img = item.querySelector('.event-img-wrap img, img');
        let thumbnail = img ? (img.getAttribute('src') || '') : '';
        if (thumbnail && thumbnail.startsWith('/')) thumbnail = BASE + thumbnail;

        if (title || eventId) {
            results.push({
                card_company: '페이북(BC카드)',
                event_id: eventId,
                title,
                subtitle,
                date_range: '',        // 리스트 뷰에 날짜 없음
                start_date: '',
                end_date: '',
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


async def scrape_paybooc() -> list[dict]:
    """페이북(BC카드) 진행 이벤트 전체 수집 (56개 전부 초기 로드됨)"""
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

        # 총 건수 확인
        total_text = await page.evaluate(
            "() => { const m = document.body.innerText.match(/총\\\\s*(\\\\d+)\\\\s*개/); return m ? m[0] : ''; }"
        )
        print(f"    페이지 총 건수 텍스트: {total_text}")

        # 이벤트 추출 (전체 로드됨)
        events = await page.evaluate(_EXTRACT_JS)
        for e in events:
            uid = e.get("event_id") or (e["title"] + e.get("start_date", ""))
            if uid and uid not in seen_ids:
                all_events.append(e)
                seen_ids.add(uid)

        print(f"    추출 완료: {len(all_events)}건")

        await context.close()
        await browser.close()

    return all_events


# ─── JS: 현재 로드된 이벤트 목록 추출 ────────────────────────────────────────
_EXTRACT_JS = """
() => {
    const now = new Date().toISOString();
    const results = [];

    // 이벤트 상세 링크 기준으로 탐색 (href에 evnt-dts 포함)
    const anchors = Array.from(
        document.querySelectorAll('a[href*="evnt-dts"], a[href*="evnt-dtl"], a[href*="evntNo"]')
    );

    // 대안: 이벤트 번호 파라미터를 포함한 모든 앵커
    const altAnchors = anchors.length > 0
        ? anchors
        : Array.from(document.querySelectorAll('a[href*="pybcUnifEvntNo"]'));

    const allAnchors = altAnchors.length > 0 ? altAnchors : anchors;

    allAnchors.forEach(anchor => {
        const href = anchor.getAttribute('href') || '';
        const url = href.startsWith('http') ? href : BASE_URL + href;
        const BASE_URL = 'https://web.paybooc.co.kr';
        const fullUrl = href.startsWith('http') ? href : (BASE_URL + href);

        // 이벤트 번호 추출
        const numMatch = href.match(/pybcUnifEvntNo=([\\w]+)/);
        const eventId = numMatch ? numMatch[1] : '';

        const container = anchor.closest('li') || anchor.closest('article') || anchor.closest('div') || anchor;

        // ── 제목 ─────────────────────────────────────────────────────────
        let title = '';
        const titleEl = container.querySelector(
            '.tit, .title, .evtTit, strong, h3, h4, [class*="tit"], [class*="title"], p'
        );
        if (titleEl) {
            title = titleEl.textContent.trim().replace(/\\s+/g, ' ');
        }
        if (!title) {
            title = anchor.textContent.trim().replace(/\\s+/g, ' ')
                .replace(/\\d{4}\\.\\d{2}\\.\\d{2}.*/, '').trim();
        }

        // ── 날짜 ─────────────────────────────────────────────────────────
        let dateRange = '';
        const dateEl = container.querySelector('.date, .period, .term, [class*="date"]');
        if (dateEl) {
            dateRange = dateEl.textContent.trim().replace(/\\s+/g, ' ');
        }
        if (!dateRange) {
            const dm = (container.textContent || '').match(
                /(\\d{4}\\.\\d{2}\\.\\d{2})[~\\-\\s]+(\\d{4}\\.\\d{2}\\.\\d{2})/
            );
            if (dm) dateRange = dm[0].replace(/\\s+/g, '').replace('-', '~');
        }

        // ── 카테고리 ─────────────────────────────────────────────────────
        const categories = Array.from(
            container.querySelectorAll('.tag, .badge, .cate, .category, [class*="tag"], [class*="cate"]')
        ).map(el => el.textContent.trim()).filter(Boolean);

        // ── 썸네일 ────────────────────────────────────────────────────────
        const img = container.querySelector('img');
        let thumbnail = img
            ? (img.getAttribute('data-src') || img.getAttribute('src') || '')
            : '';
        if (thumbnail && thumbnail.startsWith('/')) {
            thumbnail = 'https://web.paybooc.co.kr' + thumbnail;
        }

        const dm2 = dateRange.replace(/\\s/g, '').match(
            /(\\d{4}\\.\\d{2}\\.\\d{2})[~\\-](\\d{4}\\.\\d{2}\\.\\d{2})/
        );

        if (title || eventId) {
            results.push({
                card_company: '페이북(BC카드)',
                event_id: eventId,
                title,
                subtitle: '',
                date_range: dateRange,
                start_date: dm2 ? dm2[1] : '',
                end_date:   dm2 ? dm2[2] : '',
                categories,
                like_count: 0,
                thumbnail,
                url: fullUrl || href,
                scraped_at: now,
            });
        }
    });

    return results;
}
"""

# ─── JS: 총 이벤트 건수 확인 ─────────────────────────────────────────────────
_COUNT_JS = """
() => {
    // '총 N개' 패턴 탐색
    const allText = document.body.innerText;
    const match = allText.match(/총\\s*(\\d+)\\s*개/);
    return match ? parseInt(match[1]) : 0;
}
"""


async def _scroll_to_load_all(page: Page, expected_count: int = 0) -> None:
    """스크롤을 반복해 Lazy Loading으로 모든 이벤트를 로드"""
    prev_height = 0
    no_change_count = 0

    while True:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1200)

        new_height = await page.evaluate("document.body.scrollHeight")

        # '더보기' 버튼이 있으면 클릭
        more_btn = await page.query_selector(
            "button.btn_more, a.btn_more, [class*='more']:not([class*='no-more'])"
        )
        if more_btn:
            try:
                await more_btn.click()
                await page.wait_for_timeout(1200)
            except Exception:
                pass

        if new_height == prev_height:
            no_change_count += 1
            if no_change_count >= 3:
                break
        else:
            no_change_count = 0

        prev_height = new_height

        # 목표 건수 도달 확인
        if expected_count > 0:
            current = await page.evaluate(
                "() => document.querySelectorAll('a[href*=\"evnt-dts\"], a[href*=\"pybcUnifEvntNo\"]').length"
            )
            if current >= expected_count:
                break


async def scrape_paybooc() -> list[dict]:
    """페이북(BC카드) 진행 이벤트 전체 수집 (Lazy Loading 포함)"""
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

        # 총 건수 확인
        expected = await page.evaluate(_COUNT_JS)
        print(f"    예상 총 건수: {expected}건")

        # 스크롤로 전체 로드
        print("    Lazy Loading 스크롤 중…")
        await _scroll_to_load_all(page, expected_count=expected)

        # 이벤트 추출
        events = await page.evaluate(_EXTRACT_JS)
        for e in events:
            uid = e.get("event_id") or (e["title"] + e.get("start_date", ""))
            if uid and uid not in seen_ids:
                all_events.append(e)
                seen_ids.add(uid)

        print(f"    추출 완료: {len(all_events)}건")

        await context.close()
        await browser.close()

    return all_events
