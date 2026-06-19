"""
상세 혜택 스크래핑 + 카테고리 분류
- KB국민카드 : HBBMCXCRVNEC0001?mainCC=a&eventNum=X → h3 '내용' 섹션 추출
- 페이북(BC카드) : detail URL → div.event-cont 의 "혜택" 섹션
- 롯데카드   : LPBNFDA_V300.lc?evnBultSeq=X → .eventDetail 컨테이너
- 삼성카드   : UHPPBE1403M0.jsp?cms_id=X → .evtDetailCont / .cont_wrap
결과: output/events_detailed_YYYYMMDD_HHMMSS.json
"""
import asyncio
import json
import glob
import os
import re
from datetime import datetime
from playwright.async_api import async_playwright

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
CONCURRENCY = 6          # 동시 브라우저 탭 수
DETAIL_TIMEOUT = 18000   # ms

# ─── 카테고리 분류 규칙 (우선순위 순) ──────────────────────────────────────
CATEGORY_RULES = [
    ("여행", [
        "여행", "해외", "항공", "항공권", "호텔", "숙박", "리조트", "펜션", "투어",
        "크루즈", "면세점", "면세", "에어비앤비", "트립닷컴", "아고다", "호텔스닷컴",
        "라쿠텐트래블", "렌탈카스닷컴", "에어알로", "클룩", "웹투어", "와이페이모어",
        "레고랜드", "에버랜드", "롯데월드", "놀이공원", "테마파크",
        "일본", "유럽", "미국", "중국", "태국", "싱가포르", "하와이",
        "나리타", "하네다", "오사카", "후쿠오카", "파리", "런던", "바르셀로나",
        "홍콩", "마카오", "코나", "발리", "태국여행", "관광",
        "비스터", "라발레", "라로카", "ihg", "프리퍼드호텔",
        "펜타포트", "페스티벌", "국내선", "국제선",
    ]),
    ("외식", [
        "외식", "식당", "레스토랑", "카페", "커피", "치킨", "피자", "배달",
        "버거", "스타벅스", "맥도날드", "푸드", "맛집", "메가mgc커피",
        "교촌허니콤보", "다이닝", "스테이크", "스시", "라멘",
        "수블리엠", "이자카야", "쿠팡이츠", "배달의민족",
    ]),
    ("교통", [
        "주유", "주유소", "주유권", "자동차", "렌탈", "렌트",
        "택시", "고속도로", "주차", "전기차", "ev충전", "충전",
        "버스", "지하철", "기차", "철도", "고속버스",
        "해외운전", "국내선항공", "항공운임", "ev카드",
        "스피드메이트", "티스테이션", "트랩",
    ]),
    ("문화레저", [
        "문화", "공연", "영화", "도서", "음악", "전시", "스포츠",
        "레저", "골프", "야구", "cgv", "메가박스", "볼링",
        "당첨확인", "콘서트", "미술관", "박물관",
        "두산베어스", "펜타포트", "인천펜타포트", "락페스티벌",
        "월드컵", "응원키트", "운동권",
    ]),
    ("헬스뷰티", [
        "헬스", "뷰티", "화장품", "피부", "미용",
        "헬스장", "피트니스", "요가", "필라테스", "올리브영",
        "다이소", "임산", "병원", "약국", "의료",
        "마스크팩", "마스크", "스킨케어",
    ]),
    ("디지털통신", [
        "디지털", "통신", "휴대폰", "전자", "휴대폰포로콘",
        "게임", "ott", "스트리밍", "인터넷", "넷플릭스",
        "구독", "앱", "sk", "kt", "lg유플", "skt", "kt스카이라이프",
        "단말기", "t라이트", "liivmii", "lg헬로비전",
        "케이블tv", "ai플랫폼", "ai활용", "인터넷전화",
        "휴대폰 단말기", "단말기값", "esim", "데이터 로밍",
    ]),
    ("금융할부", [
        "무이자", "할부", "보험", "대출", "연회비",
        "마일리지", "리워드", "포인트적립", "포인트리",
        "포인트 제공", "h.point", "삼성화재", "현대화재",
        "자동차보험", "미니코부매스터", "파이낸싱", "시세로인튀리튬",
        "정기결제", "자동납부", "적립마일리지", "p마일리지",
        "국세", "지방세", "소상공인", "연회비 100%",
    ]),
    ("쇼핑", [
        "백화점", "마트", "온라인쇼핑", "이마트", "롯데마트",
        "홈플러스", "g마켓", "쿠팡", "11번가", "아울렛",
        "시세이즈마션", "로드샵시쿠니승마승",
        "뷔스트마션", "히아 레이드스마선",
        "쇼핑", "클리어마션", "h.이포인트", "쿠팡와우",
        "네이버플러스스토어", "슬포츠마존",
        "시세통통말이제도", "무통보너스마스터",
        "비스터업설그라니스포리툼",
    ]),
    ("생활편의", [
        "편의점", "교육", "학원", "세탁", "구청요금",
        "cu", "gs25", "세븐일레븐", "미니스톱", "이마트24",
        "세븐일레븐", "팸샵", "주거", "화백",
        "캐릭팩키지", "중국집데일레븐",
    ]),
    ("시즌취미", [
        "시즌", "문화상품권", "도서제당",
        "스탬프", "월드컵", "운동원",
        "여름", "겨울", "보열스노우파트 코리아",
        "새해", "추석", "설날", "summer", "winter",
        "황금연휴", "명절", "발렌타인",
    ]),
]

def categorize(event: dict) -> str:
    text = " ".join([
        event.get("title", ""),
        event.get("subtitle", ""),
        event.get("benefit_summary", ""),
        " ".join(event.get("categories", [])),
    ]).lower()
    # 원래 categories 도 고려 (롯데카드는 원래 카테고리 태그 존재)
    lotte_cats = " ".join(event.get("categories", [])).lower()
    if "레저" in lotte_cats or "여행" in lotte_cats:
        text += " 여행 레저"
    if "외식" in lotte_cats or "쇼핑" in lotte_cats:
        text += " 외식 쇼핑"
    if "자동차" in lotte_cats or "보험" in lotte_cats:
        text += " 자동차 보험 교통"
    for cat, keywords in CATEGORY_RULES:
        if any(kw in text for kw in keywords):
            return cat
    return "기타"


# ─── 혜택 요약 추출 헬퍼 ────────────────────────────────────────────────────
NUM_RE = re.compile(r"[\d,]+\s*(%|원|배|회|포인트|캐시백|할인|적립|쿠폰|천원|만원|달러|마일)")

def best_benefit_line(lines: list[str]) -> str:
    """수치가 포함된 가장 informative한 줄 반환"""
    scored = []
    for line in lines:
        line = line.strip()
        if len(line) < 6 or len(line) > 250:
            continue
        # 노이즈 필터
        if any(x in line for x in ["Copyright", "©", "로그인", "회원가입", "전체메뉴", "홈으로"]):
            continue
        nc = len(NUM_RE.findall(line))
        bc = sum(1 for k in ["할인", "적립", "혜택", "지급", "증정", "무이자", "캐시백"] if k in line)
        if nc + bc > 0:
            scored.append((nc * 3 + bc * 2, line))
    scored.sort(reverse=True)
    if scored:
        return scored[0][1][:200]
    # 수치 없으면 첫 의미있는 줄
    for line in lines:
        line = line.strip()
        if len(line) >= 10 and not any(x in line for x in ["©", "로그인", "전체메뉴"]):
            return line[:150]
    return ""


# ─── KB국민카드 상세 JS ──────────────────────────────────────────────────────
# h3 태그 '내용' 섹션의 다음 형제 요소들 텍스트 추출
KB_DETAIL_JS = """
() => {
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

# ─── 롯데카드 상세 JS ──────────────────────────────────────────────────────
LOTTE_DETAIL_JS = """
() => {
    // .eventDetail 컨테이너에서 혜택 섹션 추출
    const wrap = document.querySelector('.eventDetail');
    if (!wrap) return '';
    const text = wrap.innerText || '';
    // 혜택 키워드 이후 텍스트
    const idx = text.indexOf('혜택');
    if (idx >= 0) {
        return text.substring(idx + 2, idx + 600).trim();
    }
    return text.slice(0, 500).trim();
}
"""

# ─── 삼성카드 상세 JS ──────────────────────────────────────────────────────
SAMSUNG_DETAIL_JS = """
() => {
    // 삼성카드 상세 페이지 컨테이너 후보들
    const selectors = [
        '.evtDetailCont', '.cont_wrap', '.event-detail-wrap',
        '.event_detail', '#event_detail', 'article.event',
        '.inner_event', '.sec_event', '.event-body'
    ];
    for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el && el.innerText && el.innerText.length > 50) {
            const text = el.innerText;
            const idx = text.indexOf('혜택');
            if (idx >= 0) return text.substring(idx + 2, idx + 500).trim();
            return text.slice(0, 400).trim();
        }
    }
    // fallback: 본문 영역 전체 텍스트
    const body = document.body?.innerText || '';
    const idx = body.indexOf('혜택');
    if (idx > 0) return body.substring(idx + 2, idx + 400).trim();
    return '';
}
"""

# ─── 페이북 상세 JS ──────────────────────────────────────────────────────────
PAYBOOC_DETAIL_JS = """
() => {
    const cont = document.querySelector('.event-cont, .event-reform, .event-inner-container');
    if (!cont) return '';
    const text = cont.innerText;
    // "혜택" 섹션 이후 텍스트
    const idx = text.indexOf('혜택');
    if (idx >= 0) {
        const after = text.substring(idx + 2).trim();
        return after.split('\\n').filter(l => l.trim().length > 3).slice(0, 6).join(' / ');
    }
    // fallback: 전체 중 수치 포함 줄
    return text.split('\\n').filter(l => /\\d+/.test(l)).slice(0, 4).join(' / ');
}
"""


# ─── 회사별 스크래핑 함수 ────────────────────────────────────────────────────
async def fetch_kb(page, url: str) -> str:
    await page.goto(url, wait_until="domcontentloaded", timeout=DETAIL_TIMEOUT)
    await page.wait_for_timeout(1200)
    raw = await page.evaluate(KB_DETAIL_JS)
    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    return best_benefit_line(lines)


async def fetch_lotte(page, url: str) -> str:
    await page.goto(url, wait_until="domcontentloaded", timeout=DETAIL_TIMEOUT)
    await page.wait_for_timeout(1500)
    raw = await page.evaluate(LOTTE_DETAIL_JS)
    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    return best_benefit_line(lines)


async def fetch_samsung(page, url: str) -> str:
    await page.goto(url, wait_until="domcontentloaded", timeout=DETAIL_TIMEOUT)
    await page.wait_for_timeout(2000)
    raw = await page.evaluate(SAMSUNG_DETAIL_JS)
    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    return best_benefit_line(lines)


async def fetch_paybooc(page, url: str) -> str:
    await page.goto(url, wait_until="networkidle", timeout=DETAIL_TIMEOUT)
    await page.wait_for_timeout(1500)
    raw = await page.evaluate(PAYBOOC_DETAIL_JS)
    lines = [l.strip() for l in raw.replace(" / ", "\n").split("\n") if l.strip()]
    return best_benefit_line(lines)


def benefit_from_title(event: dict) -> str:
    """타이틀에서 혜택 추출 (롯데/삼성은 타이틀 자체가 혜택 설명)"""
    title = event.get("title", "").strip()
    subtitle = event.get("subtitle", "").strip()
    # 타이틀에 수치가 있으면 바로 사용
    if NUM_RE.search(title):
        return (title + (" - " + subtitle if subtitle else ""))[:200]
    # subtitle에 수치가 있으면
    if subtitle and NUM_RE.search(subtitle):
        return (subtitle + " (" + title[:60] + ")")[:200]
    # 둘 다 수치 없으면 그냥 조합
    combined = title + (" - " + subtitle if subtitle else "")
    return combined[:200]


# ─── 단일 이벤트 처리 ────────────────────────────────────────────────────────
async def process_one(sem, context, event: dict, idx: int, total: int) -> dict:
    async with sem:
        company = event.get("card_company", "")
        title   = event.get("title", "")
        url     = event.get("url", "")

        # 롯데/삼성 상세 페이지 스크래핑 추가
        page = await context.new_page()
        try:
            if company == "KB국민카드":
                summary = await fetch_kb(page, url)
            elif company == "롯데카드":
                summary = await fetch_lotte(page, url)
            elif company == "삼성카드":
                summary = await fetch_samsung(page, url)
            else:  # 페이북(BC카드)
                summary = await fetch_paybooc(page, url)

            if not summary:
                summary = benefit_from_title(event)

            event["benefit_summary"] = summary
            event["category_new"]    = categorize(event)
            print(f"  [{idx+1:3}/{total}] {company[:4]} | {summary[:55]}")

        except Exception as e:
            event["benefit_summary"] = benefit_from_title(event)
            event["category_new"]    = categorize(event)
            print(f"  [{idx+1:3}/{total}] ❌ {company[:4]} | {str(e)[:50]}")
        finally:
            await page.close()

        return event


# ─── 메인 ────────────────────────────────────────────────────────────────────
async def main() -> str:
    files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "all_card_events_*.json")))
    if not files:
        raise FileNotFoundError("output/all_card_events_*.json 파일 없음")

    latest = files[-1]
    print(f"로딩: {os.path.basename(latest)}")
    raw = json.load(open(latest, encoding="utf-8"))
    all_events: list[dict] = [e for g in raw for e in g["events"]]
    total = len(all_events)

    # 4개 회사 전체 상세 페이지 스크래핑
    need_scrape = list(all_events)
    no_scrape   = []

    print(f"상세 스크래핑: {len(need_scrape)}건 (전체)")

    # 롯데/삼성 먼저 처리 (sync)
    for e in no_scrape:
        e["benefit_summary"] = benefit_from_title(e)
        e["category_new"]    = categorize(e)

    # KB·페이북·롯데·삼성 async 스크래핑
    scraped: list[dict] = []
    if need_scrape:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 900},
                extra_http_headers={"Accept-Language": "ko-KR,ko;q=0.9"},
            )
            sem = asyncio.Semaphore(CONCURRENCY)
            tasks = [
                process_one(sem, context, e, i, len(need_scrape))
                for i, e in enumerate(need_scrape)
            ]
            scraped = list(await asyncio.gather(*tasks))
            await context.close()
            await browser.close()

    # 합치기 (원본 순서 유지)
    enriched_map = {id(e): e for e in scraped + no_scrape}
    enriched = [enriched_map.get(id(e), e) for e in all_events]

    # 저장
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUTPUT_DIR, f"events_detailed_{ts}.json")
    json.dump(enriched, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # 카테고리별 통계
    from collections import Counter
    cat_counts = Counter(e.get("category_new", "기타") for e in enriched)
    print(f"\n✅ 저장: {os.path.basename(out_path)} ({len(enriched)}건)")
    print("카테고리별 분포:")
    for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat:10s}: {cnt}건")

    return out_path


if __name__ == "__main__":
    asyncio.run(main())
