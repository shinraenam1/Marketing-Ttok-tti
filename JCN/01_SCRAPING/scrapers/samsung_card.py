"""
삼성카드 이벤트 스크래퍼
URL  : https://www.samsungcard.com/personal/event/ing/UHPPBE1401M0.jsp
방식 : 이전/다음 페이지 버튼 클릭 (표준 페이징)

실제 DOM 구조 (디버그로 확인):
  <li>
    <a href="javascript:$.noop();" class="m_link"
       onclick="javascript:UHPPBE1401M0_EVENT.GoDtlBrws('3748014', '00', 'N');">
      <span class="like"><span class="hide">좋아요 갯수</span>1</span>
      <div class="img">
        <img src="//static11.samsungcard.com/.../P_thumb_286x275_2.png" class="p_display">
        <img src="//static11.samsungcard.com/.../M_thumb_320x320_2.png" class="m_display">
      </div>
      <div class="cont">
        <p class="tit">캐비 미리 준비하면 최대 59% 할인</p>
        <span class="date">2026.06.19~2026.08.30</span>
      </div>
    </a>
  </li>
  → 이벤트 ID: onclick의 GoDtlBrws('3748014', ...) 에서 추출
  → URL: /personal/event/ing/UHPPBE0202M0.jsp?evtId=3748014
"""

from playwright.async_api import async_playwright, Page

LIST_URL = "https://www.samsungcard.com/personal/event/ing/UHPPBE1401M0.jsp"
BASE_URL = "https://www.samsungcard.com"

# ─── JS: 현재 페이지 이벤트 추출 ────────────────────────────────────────────
_EXTRACT_JS = """
() => {
    const now = new Date().toISOString();
    const results = [];
    const BASE = 'https://www.samsungcard.com';

    // a.m_link 를 기준으로 이벤트 탐색 (onclick에 GoDtlBrws 포함)
    const anchors = Array.from(document.querySelectorAll('a.m_link[onclick*="GoDtlBrws"]'));

    // 대안: onclick 기반 탐색
    const altAnchors = anchors.length > 0
        ? anchors
        : Array.from(document.querySelectorAll('a[onclick*="GoDtlBrws"]'));

    if (altAnchors.length === 0) return results;

    altAnchors.forEach(anchor => {
        // ── 이벤트 ID (GoDtlBrws 1번째 파라미터) ────────────────────────────
        const onclick = anchor.getAttribute('onclick') || '';
        const idMatch = onclick.match(/GoDtlBrws\\s*\\(\\s*'([^']+)'/);
        const eventId = idMatch ? idMatch[1] : '';
        const url = eventId
            ? `${BASE}/personal/event/ing/UHPPBE1403M0.jsp?cms_id=${eventId}`
            : '';

        // ── 제목 (.cont .tit) ────────────────────────────────────────────────
        const titEl = anchor.querySelector('.cont .tit, .tit, p.tit');
        const title = titEl ? titEl.textContent.trim().replace(/\\s+/g, ' ') : '';

        // ── 날짜 (.cont .date, span.date) ───────────────────────────────────
        const dateEl = anchor.querySelector('.cont .date, span.date, .date');
        let dateRange = dateEl ? dateEl.textContent.trim() : '';
        if (!dateRange) {
            const dm = (anchor.textContent || '').match(
                /(\\d{4}\\.\\d{2}\\.\\d{2})[~\\-](\\d{4}\\.\\d{2}\\.\\d{2})/
            );
            if (dm) dateRange = dm[0];
        }

        // ── 좋아요 수 (span.like 내 숫자) ───────────────────────────────────
        const likeEl = anchor.querySelector('span.like, .like_cnt, [class*="like"]');
        let likeCount = 0;
        if (likeEl) {
            // "좋아요 갯수" 텍스트 제거 후 숫자만 추출
            const likeText = likeEl.textContent.replace('좋아요 갯수', '').trim();
            const m = likeText.match(/\\d+/);
            if (m) likeCount = parseInt(m[0]);
        }

        // ── 썸네일 (.img img.p_display 또는 첫 img) ─────────────────────────
        const img = anchor.querySelector('.img img.p_display, .img img, img');
        let thumbnail = img ? (img.getAttribute('src') || '') : '';
        if (thumbnail && thumbnail.startsWith('//'))  thumbnail = 'https:' + thumbnail;
        if (thumbnail && thumbnail.startsWith('/'))   thumbnail = BASE + thumbnail;

        // ── 날짜 파싱 ─────────────────────────────────────────────────────────
        const dm2 = dateRange.replace(/\\s/g, '').match(
            /(\\d{4}\\.\\d{2}\\.\\d{2})[~\\-](\\d{4}\\.\\d{2}\\.\\d{2})/
        );

        if (title || eventId) {
            results.push({
                card_company: '삼성카드',
                event_id: eventId,
                title,
                subtitle: '',
                date_range: dateRange,
                start_date: dm2 ? dm2[1] : '',
                end_date:   dm2 ? dm2[2] : '',
                categories: [],
                like_count: likeCount,
                thumbnail,
                url,
                scraped_at: now,
            });
        }
    });

    return results;
}
"""

# ─── JS: 다음 페이지 이동 ────────────────────────────────────────────────────
_NEXT_PAGE_JS = """
() => {
    // 삼성카드 페이지네이션: '다음' 텍스트 또는 class 탐색
    const nextSelectors = [
        'a.btn_next', 'button.btn_next',
        'a[class*="next"]', 'button[class*="next"]',
        'a[title*="다음"]', 'button[title*="다음"]',
        '.paging .next', '.pagination .next',
    ];

    for (const sel of nextSelectors) {
        const btn = document.querySelector(sel);
        if (btn) {
            const style = window.getComputedStyle(btn);
            const isDisabled = btn.disabled ||
                btn.classList.contains('disabled') ||
                btn.getAttribute('aria-disabled') === 'true';
            if (style.display !== 'none' && !isDisabled) {
                btn.click();
                return true;
            }
        }
    }

    // 텍스트 기반 탐색
    for (const el of document.querySelectorAll('a, button')) {
        const txt = el.textContent.trim();
        if (txt === '다음' || txt === '다음으로' || txt === 'next') {
            const style = window.getComputedStyle(el);
            const isDisabled = el.disabled || el.classList.contains('disabled');
            if (style.display !== 'none' && !isDisabled) {
                el.click();
                return true;
            }
        }
    }

    return false;
}
"""

# ─── JS: 이벤트 URL 네트워크 인터셉트 방식으로 보완 ─────────────────────────
_GET_FIRST_EVENT_URL_JS = """
() => {
    // 첫 번째 이벤트 앵커 클릭 후 URL 패턴 파악용
    const anchor = document.querySelector('a[href*="javascript:$.noop"], a[href*="$.noop"]');
    if (!anchor) return null;
    return anchor.outerHTML.substring(0, 300);
}
"""


async def _try_get_event_urls(page: Page, events: list[dict]) -> list[dict]:
    """
    이벤트 URL이 없는 경우 첫 이벤트를 클릭해 URL 패턴 파악 후 보완.
    모든 URL을 클릭으로 탐색하면 너무 느리므로 패턴 파악만 수행.
    """
    no_url_count = sum(1 for e in events if not e.get("url"))
    if no_url_count == 0:
        return events  # 이미 모두 URL 있음

    # 페이지에서 직접 JS 변수로 이벤트 목록 탐색
    js_data = await page.evaluate("""
    () => {
        // 전역 JS 변수에서 이벤트 데이터 탐색
        const candidates = ['evtList', 'eventList', 'evntList', 'dataList', 'listData'];
        for (const key of candidates) {
            if (window[key] && Array.isArray(window[key]) && window[key].length > 0) {
                return window[key].slice(0, 3);  // 샘플만
            }
        }
        return null;
    }
    """)

    if js_data:
        print(f"    JS 변수에서 이벤트 데이터 발견: {js_data[0] if js_data else ''}")

    return events


async def scrape_samsung_card() -> list[dict]:
    """삼성카드 진행 이벤트 전체 수집 (페이지 이동 포함)"""
    all_events: list[dict] = []
    seen_titles: set[str] = set()

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

        # 네트워크 응답 인터셉트 (JSON API 탐색)
        event_api_urls: list[str] = []

        async def on_response(response):
            ct = response.headers.get("content-type", "")
            if "json" in ct and "/event" in response.url and response.status == 200:
                event_api_urls.append(response.url)

        page.on("response", on_response)

        print(f"    접속: {LIST_URL}")
        await page.goto(LIST_URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        if event_api_urls:
            print(f"    이벤트 API 발견: {event_api_urls[:2]}")

        page_num = 1
        consecutive_empty = 0

        while True:
            print(f"    [{page_num}페이지] 파싱 중…", end=" ")
            events = await page.evaluate(_EXTRACT_JS)

            # URL 보완 시도
            events = await _try_get_event_urls(page, events)

            added = 0
            for e in events:
                uid = e["title"] + e.get("start_date", "")
                if uid and uid not in seen_titles:
                    all_events.append(e)
                    seen_titles.add(uid)
                    added += 1

            print(f"{added}건 신규 / 누계 {len(all_events)}건")

            if added == 0:
                consecutive_empty += 1
                if consecutive_empty >= 2:
                    print("    연속 2회 신규 없음 → 종료")
                    break
            else:
                consecutive_empty = 0

            moved = await page.evaluate(_NEXT_PAGE_JS)
            if not moved:
                print("    다음 페이지 버튼 없음 → 종료")
                break

            await page.wait_for_timeout(2500)
            page_num += 1

        await context.close()
        await browser.close()

    return all_events
