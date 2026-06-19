"""
카테고리별 이벤트 리포트 HTML 생성기
결과: report.html  (단순 텍스트 목록 형식)
"""
import json
import glob
import os
from datetime import datetime
from html import escape as esc

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

# ── 최신 enriched 파일 로딩 ──────────────────────────────────────────────────
files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "events_detailed_*.json")))
if not files:
    raise FileNotFoundError("output/events_detailed_*.json 파일 없음. scrape_details.py 먼저 실행하세요.")

latest = files[-1]
data: list[dict] = json.load(open(latest, encoding="utf-8"))
print(f"로딩: {os.path.basename(latest)} ({len(data)}건)")

# ── 카테고리 순서 ────────────────────────────────────────────────────────────
CATEGORIES = [
    ("쇼핑",       "🛍️"),
    ("외식",       "🍽️"),
    ("여행",       "✈️"),
    ("생활편의",   "🏠"),
    ("교통",       "🚗"),
    ("문화레저",   "🎭"),
    ("금융할부",   "💰"),
    ("헬스뷰티",   "💄"),
    ("디지털통신", "💻"),
    ("시즌취미",   "🎉"),
    ("기타",       "📌"),
]

# 카테고리별 그룹핑
groups: dict[str, list[dict]] = {c: [] for c, _ in CATEGORIES}
for e in data:
    cat = e.get("category_new", "기타")
    if cat not in groups:
        cat = "기타"
    groups[cat].append(e)

total = len(data)
date_str = datetime.now().strftime("%Y.%m.%d %H:%M")

# 회사별 색상
CO_COLOR = {
    "KB국민카드":    "#f59e0b",
    "페이북(BC카드)": "#10b981",
    "롯데카드":      "#ef4444",
    "삼성카드":      "#3b82f6",
}

def co_badge(company: str) -> str:
    color = CO_COLOR.get(company, "#6366f1")
    return f'<span class="badge" style="background:{color}">{esc(company)}</span>'

def row_html(e: dict) -> str:
    company  = e.get("card_company", "")
    title    = e.get("title", "").replace("\n", " ").strip()
    subtitle = e.get("subtitle", "").strip()
    benefit  = e.get("benefit_summary", "").replace("\n", " ").strip()
    date_r   = e.get("date_range", "")
    url      = e.get("url", "")

    display_title = title
    if subtitle and subtitle != title:
        display_title = f"{title} — {subtitle}"

    benefit_html = esc(benefit) if benefit else '<span class="no-benefit">혜택 정보 없음</span>'
    date_html = f'<span class="date">📅 {esc(date_r)}</span>' if date_r else ""
    link_html = (
        f'<a href="{esc(url)}" target="_blank" rel="noopener" class="url-link">상세 →</a>'
        if url else '<span class="no-url">-</span>'
    )

    return f"""
      <div class="row">
        <div class="row-left">
          {co_badge(company)}
          <span class="ev-title">{esc(display_title)}</span>
        </div>
        <div class="row-benefit">{benefit_html}</div>
        <div class="row-meta">
          {date_html}
          {link_html}
        </div>
      </div>"""

# ── 카테고리 섹션 HTML 조합 ──────────────────────────────────────────────────
sections_html = ""
for cat, emoji in CATEGORIES:
    events = groups.get(cat, [])
    if not events:
        continue
    rows = "".join(row_html(e) for e in events)
    sections_html += f"""
  <section class="cat-section" id="cat-{cat}">
    <div class="cat-header">
      <span class="cat-emoji">{emoji}</span>
      <span class="cat-name">{cat}</span>
      <span class="cat-count">{len(events)}건</span>
    </div>
    <div class="rows">{rows}
    </div>
  </section>"""

# ── TOC ──────────────────────────────────────────────────────────────────────
toc_items = ""
for cat, emoji in CATEGORIES:
    cnt = len(groups.get(cat, []))
    if cnt:
        toc_items += f'<a href="#cat-{cat}" class="toc-item">{emoji} {cat} <span>{cnt}</span></a>'

# ── 최종 HTML ────────────────────────────────────────────────────────────────
HTML = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>카드사 이벤트 현황 리포트 — {date_str}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg: #f8fafc;
      --card: #fff;
      --border: #e2e8f0;
      --text: #1e293b;
      --sub: #64748b;
      --primary: #1a56db;
      --row-hover: #f0f9ff;
    }}
    body {{
      font-family: 'Pretendard', 'Apple SD Gothic Neo', -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      font-size: 14px;
      line-height: 1.6;
    }}

    /* 헤더 */
    header {{
      background: linear-gradient(135deg, #1e3a8a, #1a56db);
      color: #fff;
      padding: 24px 32px;
      position: sticky; top: 0; z-index: 50;
    }}
    header h1 {{ font-size: 1.25rem; font-weight: 700; }}
    header p {{ font-size: .8rem; opacity: .75; margin-top: 2px; }}

    /* TOC */
    .toc {{
      display: flex; flex-wrap: wrap; gap: 6px;
      padding: 14px 32px;
      background: #fff;
      border-bottom: 1px solid var(--border);
      position: sticky; top: 68px; z-index: 40;
    }}
    .toc-item {{
      padding: 4px 12px;
      border: 1px solid var(--border);
      border-radius: 20px;
      font-size: .78rem;
      text-decoration: none;
      color: var(--text);
      transition: all .12s;
    }}
    .toc-item:hover {{ background: var(--primary); color: #fff; border-color: var(--primary); }}
    .toc-item span {{ color: var(--sub); font-size: .72rem; }}
    .toc-item:hover span {{ color: rgba(255,255,255,.8); }}

    /* 본문 */
    main {{ padding: 24px 32px; max-width: 1200px; margin: 0 auto; }}

    /* 카테고리 섹션 */
    .cat-section {{ margin-bottom: 32px; }}
    .cat-header {{
      display: flex; align-items: center; gap: 8px;
      padding: 10px 16px;
      background: var(--primary);
      color: #fff;
      border-radius: 8px 8px 0 0;
      font-weight: 700;
      font-size: .95rem;
    }}
    .cat-emoji {{ font-size: 1.1rem; }}
    .cat-count {{ margin-left: auto; font-size: .8rem; opacity: .85; font-weight: 400; }}

    /* 이벤트 행 */
    .rows {{
      background: var(--card);
      border: 1px solid var(--border);
      border-top: none;
      border-radius: 0 0 8px 8px;
      overflow: hidden;
    }}
    .row {{
      display: grid;
      grid-template-columns: 1fr 1.4fr auto;
      gap: 12px;
      align-items: start;
      padding: 10px 16px;
      border-bottom: 1px solid var(--border);
      transition: background .1s;
    }}
    .row:last-child {{ border-bottom: none; }}
    .row:hover {{ background: var(--row-hover); }}

    .row-left {{ display: flex; align-items: flex-start; gap: 8px; flex-wrap: wrap; }}
    .badge {{
      display: inline-block;
      padding: 2px 8px; border-radius: 5px;
      font-size: .72rem; font-weight: 700; color: #fff;
      white-space: nowrap; flex-shrink: 0;
    }}
    .ev-title {{ font-size: .87rem; font-weight: 600; line-height: 1.45; }}

    .row-benefit {{ font-size: .83rem; color: var(--text); line-height: 1.5; }}
    .no-benefit {{ color: var(--sub); font-style: italic; }}

    .row-meta {{
      display: flex; flex-direction: column; gap: 4px;
      align-items: flex-end; white-space: nowrap; flex-shrink: 0;
    }}
    .date {{ font-size: .75rem; color: var(--sub); }}
    .url-link {{
      font-size: .75rem;
      color: var(--primary);
      text-decoration: none;
      font-weight: 600;
      padding: 2px 8px;
      border: 1px solid var(--primary);
      border-radius: 4px;
      transition: all .12s;
    }}
    .url-link:hover {{ background: var(--primary); color: #fff; }}
    .no-url {{ font-size: .75rem; color: var(--sub); }}

    /* 푸터 */
    footer {{
      text-align: center;
      padding: 24px;
      font-size: .78rem;
      color: var(--sub);
      border-top: 1px solid var(--border);
    }}

    @media (max-width: 700px) {{
      header, .toc, main {{ padding-left: 16px; padding-right: 16px; }}
      .row {{ grid-template-columns: 1fr; gap: 6px; }}
      .row-meta {{ align-items: flex-start; }}
      .toc {{ top: 60px; }}
    }}
  </style>
</head>
<body>
<header>
  <h1>🏦 타 카드사 이벤트 현황 리포트</h1>
  <p>기준일: {date_str} &nbsp;|&nbsp; 총 {total}건 &nbsp;|&nbsp; KB국민카드 · 페이북(BC카드) · 롯데카드 · 삼성카드</p>
</header>

<nav class="toc">{toc_items}</nav>

<main>
{sections_html}
</main>

<footer>
  수집 데이터 기준일: {date_str} &nbsp;|&nbsp; KB국민카드 · 페이북(BC카드) · 롯데카드 · 삼성카드
</footer>
</body>
</html>"""

out = os.path.join(os.path.dirname(__file__), "report.html")
open(out, "w", encoding="utf-8").write(HTML)
print(f"✅ report.html 생성 완료  ({total}건)")
print(f"   경로: {out}")

# 카테고리 요약 출력
print("\n카테고리별:")
for cat, _ in CATEGORIES:
    n = len(groups.get(cat, []))
    if n:
        print(f"  {cat:10s}: {n}건")
