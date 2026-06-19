"""
롯데카드 이벤트 스크래퍼
URL  : https://www.lottecard.co.kr/app/LPBNFDA_V100.lc
방식 : '더보기' 버튼 클릭 반복 (초기 9건 → 총 60건 기준)

실제 DOM 구조 (디버그로 확인):
  <li>
    <script>tlfLoad("1","load","11172","","","","");</script>
    <a href="javascript:tlfLoad('1','click','11172','9999','','2','N');" role="button"
       onclick="GA_EtcSvBtnEvent(...)">
      <img src="//image.lottecard.co.kr/UploadFiles/event/...png">
      <span class="eventCont">
        <b>삼성화재 내차 보험료 조회하면 네이버페이 포인트 7천원 지급</b>
        <span class="date">2026.06.01 ~ 2026.06.30</span>
      </span>
    </a>
  </li>
  → 이벤트 ID: tlfLoad 3번째 파라미터 ('11172')
  → URL: /app/LPBNFDB_V100.lc?evntNo=11172
"""

from playwright.async_api import async_playwright, Page

LIST_URL = "https://www.lottecard.co.kr/app/LPBNFDA_V100.lc"
BASE_URL = "https://www.lottecard.co.kr"

# ─── JS: 현재 로드된 이벤트 목록 추출 ────────────────────────────────────────
_EXTRACT_JS = """
() => {
    const now = new Date().toISOString();
    const results = [];
    const BASE = 'https://www.lottecard.co.kr';

    // tlfLoad href를 가진 앵커가 있는 li 탐색
    const anchors = Array.from(document.querySelectorAll('a[href*="tlfLoad"]'));
    if (anchors.length === 0) return results;

    anchors.forEach(anchor => {
        // ── 이벤트 ID + 카테고리 + 탭 (tlfLoad 3,4,6번째 파라미터) ────────────
        const href = anchor.getAttribute('href') || '';
        // tlfLoad('1','click','11172','9999','','2','N')
        const tlMatch = href.match(/tlfLoad\s*\([^)]+\)/);
        let eventId = '', ctgSeq = '9999', bigTab = '2';
        if (tlMatch) {
            const params = tlMatch[0].match(/'([^']*)'/g) || [];
            eventId = params[2] ? params[2].replace(/'/g,'') : '';
            ctgSeq  = params[3] ? params[3].replace(/'/g,'') : '9999';
            bigTab  = params[5] ? params[5].replace(/'/g,'') : '2';
        }
        const url = eventId
            ? `${BASE}/app/LPBNFDA_V300.lc?evnBultSeq=${eventId}&evnCtgSeq=${ctgSeq}&bigTabGubun=${bigTab}`
            : '';

        // ── 제목 (.eventCont b) ──────────────────────────────────────────────
        const titEl = anchor.querySelector('.eventCont b, b');
        const title = titEl ? titEl.textContent.trim().replace(/\\s+/g, ' ') : '';

        // ── 날짜 (.eventCont span.date) ──────────────────────────────────────
        const dateEl = anchor.querySelector('.eventCont .date, .date, span.date');
        let dateRange = dateEl ? dateEl.textContent.trim().replace(/\\s+/g, ' ') : '';
        // 날짜 형식 정규화: "2026.06.01 ~ 2026.06.30" → "2026.06.01~2026.06.30"
        dateRange = dateRange.replace(/\\s*~\\s*/, '~');

        // ── 썸네일 ───────────────────────────────────────────────────────────
        const img = anchor.querySelector('img');
        let thumbnail = img ? (img.getAttribute('src') || '') : '';
        if (thumbnail && thumbnail.startsWith('//'))  thumbnail = 'https:' + thumbnail;
        if (thumbnail && thumbnail.startsWith('/'))   thumbnail = BASE + thumbnail;

        // ── 날짜 파싱 ─────────────────────────────────────────────────────────
        const dm2 = dateRange.replace(/\\s/g, '').match(
            /(\\d{4}\\.\\d{2}\\.\\d{2})[~\\-](\\d{4}\\.\\d{2}\\.\\d{2})/
        );

        if (title || eventId) {
            results.push({
                card_company: '롯데카드',
                event_id: eventId,
                title,
                subtitle: '',
                date_range: dateRange,
                start_date: dm2 ? dm2[1] : '',
                end_date:   dm2 ? dm2[2] : '',
                categories: [],
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

# ─── JS: 현재 로드 수 / 전체 수 확인 ────────────────────────────────────────
_COUNT_JS = """
() => {
    // '(9/60)' 또는 '9 / 60' 패턴
    const allText = document.body.innerText;
    const m = allText.match(/(\\d+)\\s*\\/\\s*(\\d+)/);
    if (m) return { current: parseInt(m[1]), total: parseInt(m[2]) };
    // '총 N개' 패턴
    const m2 = allText.match(/총\\s*(\\d+)\\s*[개건]/);
    if (m2) return { current: 0, total: parseInt(m2[1]) };
    return { current: 0, total: 0 };
}
"""

# ─── JS: 더보기 버튼 클릭 ────────────────────────────────────────────────────
_CLICK_MORE_JS = """
() => {
    // 텍스트에 '더보기' 포함된 모든 클릭 가능 요소 탐색
    const clickables = Array.from(document.querySelectorAll('a, button, span[onclick], div[onclick]'));
    for (const el of clickables) {
        const txt = el.textContent.trim();
        if (!txt.includes('더보기')) continue;
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden') continue;
        if (el.disabled) continue;
        el.click();
        return true;
    }

    // class 기반 탐색
    const moreBtnSelectors = [
        'a.btn_more', 'button.btn_more',
        'a.btnMore', 'button.btnMore',
        'a[class*="more"]', 'button[class*="more"]',
        'a[onclick*="fnMore"]', 'a[onclick*="moreView"]',
    ];
    for (const sel of moreBtnSelectors) {
        const btn = document.querySelector(sel);
        if (btn) {
            const style = window.getComputedStyle(btn);
            if (style.display !== 'none' && !btn.disabled) {
                btn.click();
                return true;
            }
        }
    }
    return false;
}
"""


async def _load_all_events(page: Page) -> None:
    """'더보기' 버튼을 반복 클릭하여 전체 이벤트 로드"""
    for attempt in range(20):  # 최대 20회 (안전 상한)
        info = await page.evaluate(_COUNT_JS)
        current, total = info.get("current", 0), info.get("total", 0)
        print(f"    로드 현황: {current}/{total}  (시도 {attempt+1})")

        if total > 0 and current >= total:
            break

        clicked = await page.evaluate(_CLICK_MORE_JS)
        if not clicked:
            # 스크롤로 더보기 버튼 탐색
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(800)
            clicked = await page.evaluate(_CLICK_MORE_JS)

        if not clicked:
            break

        await page.wait_for_timeout(1500)


async def scrape_lotte_card() -> list[dict]:
    """롯데카드 진행 이벤트 전체 수집 (더보기 버튼 반복 클릭)"""
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

        print(f"    접속: {LIST_URL}")
        await page.goto(LIST_URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        # 전체이벤트 탭이 있으면 클릭
        try:
            all_tab = await page.query_selector('a:text("전체이벤트"), a:text("전체 이벤트"), #tabAll')
            if all_tab:
                await all_tab.click()
                await page.wait_for_timeout(1000)
        except Exception:
            pass

        # 더보기 반복 클릭
        await _load_all_events(page)

        # 이벤트 추출
        events = await page.evaluate(_EXTRACT_JS)
        for e in events:
            uid = e["title"] + e.get("start_date", "")
            if uid and uid not in seen_titles:
                all_events.append(e)
                seen_titles.add(uid)

        print(f"    추출 완료: {len(all_events)}건")

        await context.close()
        await browser.close()

    return all_events
