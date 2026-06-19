"""
스크래핑 데이터 뷰어 HTML 생성기
최신 all_card_events_*.json 파일을 읽어 viewer.html 생성
"""
import json
import glob
import os
import re

# ── 최신 통합 파일 찾기 ────────────────────────────────────────
output_dir = os.path.join(os.path.dirname(__file__), "output")
files = sorted(glob.glob(os.path.join(output_dir, "all_card_events_*.json")))
if not files:
    raise FileNotFoundError("output/all_card_events_*.json 파일을 찾을 수 없습니다.")

latest = files[-1]
print(f"로딩: {os.path.basename(latest)}")

raw = json.load(open(latest, encoding="utf-8"))
all_events = []
for group in raw:
    all_events.extend(group["events"])

total = len(all_events)
scraped_at = raw[0]["scraped_at"][:10] if raw else ""
print(f"총 {total}건 이벤트 로드 완료")

data_json = json.dumps(all_events, ensure_ascii=False)

# ── HTML 템플릿 ────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>타 카드사 이벤트 현황 뷰어</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg: #f0f2f5;
      --card-bg: #fff;
      --primary: #1a56db;
      --border: #e2e8f0;
      --text: #1e293b;
      --sub: #64748b;
      --shadow: 0 1px 3px rgba(0,0,0,.1), 0 1px 2px rgba(0,0,0,.06);
      --shadow-hover: 0 10px 25px rgba(0,0,0,.12);
    }}
    body {{
      font-family: 'Pretendard', 'Apple SD Gothic Neo', -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
    }}

    /* ── 헤더 ── */
    header {{
      background: linear-gradient(135deg, #1e3a8a 0%, #1a56db 100%);
      color: #fff;
      padding: 28px 32px 24px;
    }}
    header h1 {{ font-size: 1.5rem; font-weight: 700; letter-spacing: -.5px; }}
    header p {{ margin-top: 4px; opacity: .8; font-size: .875rem; }}

    /* ── 요약 카드 ── */
    .summary {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      padding: 20px 32px;
      background: #fff;
      border-bottom: 1px solid var(--border);
    }}
    .stat-card {{
      display: flex;
      align-items: center;
      gap: 12px;
      background: var(--bg);
      border-radius: 10px;
      padding: 12px 18px;
      cursor: pointer;
      transition: all .15s;
      border: 2px solid transparent;
      user-select: none;
    }}
    .stat-card:hover {{ border-color: var(--primary); }}
    .stat-card.active {{ background: #eff6ff; border-color: var(--primary); }}
    .stat-card .logo {{
      width: 40px; height: 40px; border-radius: 8px;
      display: flex; align-items: center; justify-content: center;
      font-size: 1.25rem; font-weight: 800; color: #fff;
    }}
    .stat-card .info .name {{ font-size: .8rem; color: var(--sub); }}
    .stat-card .info .num {{ font-size: 1.4rem; font-weight: 700; line-height: 1.2; }}
    .stat-card .info .num span {{ font-size: .75rem; font-weight: 400; color: var(--sub); }}

    /* ── 필터 바 ── */
    .toolbar {{
      padding: 16px 32px;
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
      background: #fff;
      border-bottom: 1px solid var(--border);
    }}
    .toolbar input[type=search] {{
      flex: 1; min-width: 200px;
      padding: 8px 14px;
      border: 1px solid var(--border);
      border-radius: 8px;
      font-size: .9rem;
      outline: none;
      transition: border-color .15s;
    }}
    .toolbar input[type=search]:focus {{ border-color: var(--primary); }}
    .tag-btn {{
      padding: 6px 14px;
      border: 1px solid var(--border);
      border-radius: 20px;
      font-size: .8rem;
      cursor: pointer;
      background: #fff;
      transition: all .15s;
    }}
    .tag-btn:hover {{ border-color: var(--primary); color: var(--primary); }}
    .tag-btn.active {{
      background: var(--primary); color: #fff; border-color: var(--primary);
    }}
    .result-count {{ margin-left: auto; font-size: .85rem; color: var(--sub); }}

    /* ── 이벤트 그리드 ── */
    .main {{ padding: 24px 32px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 18px;
    }}

    /* ── 이벤트 카드 ── */
    .event-card {{
      background: var(--card-bg);
      border-radius: 12px;
      overflow: hidden;
      box-shadow: var(--shadow);
      transition: transform .18s, box-shadow .18s;
      cursor: pointer;
      display: flex;
      flex-direction: column;
    }}
    .event-card:hover {{
      transform: translateY(-4px);
      box-shadow: var(--shadow-hover);
    }}
    .event-card .thumb {{
      position: relative;
      padding-top: 56%;
      background: #e2e8f0;
      overflow: hidden;
    }}
    .event-card .thumb img {{
      position: absolute; top: 0; left: 0;
      width: 100%; height: 100%; object-fit: cover;
    }}
    .event-card .thumb .no-img {{
      position: absolute; top: 0; left: 0;
      width: 100%; height: 100%;
      display: flex; align-items: center; justify-content: center;
      font-size: 2rem; color: #cbd5e1;
    }}
    .event-card .company-badge {{
      position: absolute; top: 8px; left: 8px;
      padding: 3px 8px; border-radius: 6px;
      font-size: .7rem; font-weight: 700; color: #fff;
    }}
    .event-card .body {{
      padding: 14px;
      flex: 1;
      display: flex; flex-direction: column; gap: 6px;
    }}
    .event-card .ev-title {{
      font-size: .9rem; font-weight: 600;
      line-height: 1.4;
      display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    .event-card .ev-subtitle {{
      font-size: .78rem; color: var(--sub);
    }}
    .event-card .ev-date {{
      font-size: .75rem; color: #94a3b8;
      margin-top: auto;
    }}
    .event-card .ev-cats {{
      display: flex; flex-wrap: wrap; gap: 4px;
    }}
    .event-card .ev-cats .cat {{
      padding: 2px 7px; border-radius: 4px;
      font-size: .7rem; background: #eff6ff; color: var(--primary);
    }}
    .event-card .ev-like {{
      font-size: .75rem; color: #f59e0b; font-weight: 600;
    }}

    /* 회사별 색상 */
    .kb   {{ background: #fbbf24; }}
    .paybooc {{ background: #10b981; }}
    .lotte {{ background: #ef4444; }}
    .samsung {{ background: #3b82f6; }}
    .other {{ background: #6366f1; }}

    /* ── 모달 ── */
    .modal-overlay {{
      display: none;
      position: fixed; inset: 0;
      background: rgba(0,0,0,.5);
      z-index: 100;
      align-items: center; justify-content: center;
    }}
    .modal-overlay.open {{ display: flex; }}
    .modal {{
      background: #fff; border-radius: 16px;
      max-width: 520px; width: 90%;
      max-height: 88vh; overflow-y: auto;
      box-shadow: 0 20px 60px rgba(0,0,0,.3);
    }}
    .modal-img {{ width: 100%; max-height: 240px; object-fit: cover; }}
    .modal-body {{ padding: 20px 24px 24px; }}
    .modal-company {{ font-size: .8rem; font-weight: 700; margin-bottom: 6px; }}
    .modal-title {{ font-size: 1.1rem; font-weight: 700; line-height: 1.5; }}
    .modal-sub {{ font-size: .88rem; color: var(--sub); margin-top: 4px; }}
    .modal-date {{ margin: 10px 0 6px; font-size: .82rem; color: #475569; }}
    .modal-date strong {{ color: var(--text); }}
    .modal-cats {{ display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px; }}
    .modal-cats .cat {{ padding: 3px 10px; border-radius: 6px; font-size: .78rem; background: #eff6ff; color: var(--primary); }}
    .modal-link {{
      display: block; text-align: center;
      background: var(--primary); color: #fff;
      padding: 11px; border-radius: 10px;
      text-decoration: none; font-weight: 600; font-size: .9rem;
      transition: opacity .15s;
    }}
    .modal-link:hover {{ opacity: .85; }}
    .modal-close {{
      float: right; cursor: pointer;
      font-size: 1.4rem; color: var(--sub);
      background: none; border: none; line-height: 1;
      padding: 4px;
    }}

    /* ── 빈 상태 ── */
    .empty {{
      text-align: center; padding: 60px 20px; color: var(--sub);
    }}
    .empty .icon {{ font-size: 3rem; }}
    .empty p {{ margin-top: 12px; }}

    @media (max-width: 600px) {{
      header, .summary, .toolbar, .main {{ padding-left: 16px; padding-right: 16px; }}
      .grid {{ grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; }}
    }}
  </style>
</head>
<body>

<header>
  <h1>🏦 타 카드사 이벤트 현황 뷰어</h1>
  <p>수집일: {scraped_at} &nbsp;|&nbsp; 총 <strong>{total}</strong>건</p>
</header>

<div class="summary">
  <div class="stat-card active" id="filter-all" onclick="filterCompany('all')">
    <div class="logo" style="background:#1a56db">전</div>
    <div class="info">
      <div class="name">전체</div>
      <div class="num" id="cnt-all">{total} <span>건</span></div>
    </div>
  </div>
  <div class="stat-card" id="filter-KB국민카드" onclick="filterCompany('KB국민카드')">
    <div class="logo kb">KB</div>
    <div class="info">
      <div class="name">KB국민카드</div>
      <div class="num" id="cnt-KB">— <span>건</span></div>
    </div>
  </div>
  <div class="stat-card" id="filter-페이북(BC카드)" onclick="filterCompany('페이북(BC카드)')">
    <div class="logo paybooc">BC</div>
    <div class="info">
      <div class="name">페이북(BC카드)</div>
      <div class="num" id="cnt-BC">— <span>건</span></div>
    </div>
  </div>
  <div class="stat-card" id="filter-롯데카드" onclick="filterCompany('롯데카드')">
    <div class="logo lotte">롯</div>
    <div class="info">
      <div class="name">롯데카드</div>
      <div class="num" id="cnt-Lotte">— <span>건</span></div>
    </div>
  </div>
  <div class="stat-card" id="filter-삼성카드" onclick="filterCompany('삼성카드')">
    <div class="logo samsung">S</div>
    <div class="info">
      <div class="name">삼성카드</div>
      <div class="num" id="cnt-Samsung">— <span>건</span></div>
    </div>
  </div>
</div>

<div class="toolbar">
  <input type="search" id="search" placeholder="이벤트 제목 검색..." oninput="render()">
  <div id="cat-filters" style="display:flex;gap:6px;flex-wrap:wrap;"></div>
  <div class="result-count" id="result-count"></div>
</div>

<div class="main">
  <div class="grid" id="grid"></div>
  <div class="empty" id="empty" style="display:none">
    <div class="icon">🔍</div>
    <p>검색 결과가 없습니다.</p>
  </div>
</div>

<!-- 모달 -->
<div class="modal-overlay" id="modal" onclick="closeModal(event)">
  <div class="modal">
    <img id="modal-img" src="" style="display:none" class="modal-img">
    <div class="modal-body">
      <button class="modal-close" onclick="closeModalDirect()">✕</button>
      <div class="modal-company" id="modal-company"></div>
      <div class="modal-title" id="modal-title"></div>
      <div class="modal-sub" id="modal-sub"></div>
      <div class="modal-date" id="modal-date"></div>
      <div class="modal-cats" id="modal-cats"></div>
      <a id="modal-link" href="#" target="_blank" rel="noopener" class="modal-link">이벤트 상세 보기 →</a>
    </div>
  </div>
</div>

<script>
const DATA = {data_json};

const COMPANY_CLASS = {{
  'KB국민카드': 'kb',
  '페이북(BC카드)': 'paybooc',
  '롯데카드': 'lotte',
  '삼성카드': 'samsung',
}};

let activeCompany = 'all';
let activeCat = 'all';

// ── 카테고리 목록 ──
const allCats = [...new Set(DATA.flatMap(e => e.categories))].sort();

// ── 카운트 초기화 ──
function initCounts() {{
  const counts = {{}};
  DATA.forEach(e => {{ counts[e.card_company] = (counts[e.card_company] || 0) + 1; }});
  document.getElementById('cnt-KB').innerHTML = (counts['KB국민카드'] || 0) + ' <span>건</span>';
  document.getElementById('cnt-BC').innerHTML = (counts['페이북(BC카드)'] || 0) + ' <span>건</span>';
  document.getElementById('cnt-Lotte').innerHTML = (counts['롯데카드'] || 0) + ' <span>건</span>';
  document.getElementById('cnt-Samsung').innerHTML = (counts['삼성카드'] || 0) + ' <span>건</span>';
}}

// ── 카테고리 버튼 생성 ──
function initCatFilters() {{
  const wrap = document.getElementById('cat-filters');
  const btn0 = document.createElement('button');
  btn0.className = 'tag-btn active'; btn0.textContent = '전체';
  btn0.dataset.cat = 'all';
  btn0.onclick = () => setCat('all');
  wrap.appendChild(btn0);

  allCats.forEach(cat => {{
    const btn = document.createElement('button');
    btn.className = 'tag-btn'; btn.textContent = cat;
    btn.dataset.cat = cat;
    btn.onclick = () => setCat(cat);
    wrap.appendChild(btn);
  }});
}}

function setCat(cat) {{
  activeCat = cat;
  document.querySelectorAll('.tag-btn').forEach(b => {{
    b.classList.toggle('active', b.dataset.cat === cat);
  }});
  render();
}}

function filterCompany(company) {{
  activeCompany = company;
  document.querySelectorAll('.stat-card').forEach(c => {{
    c.classList.toggle('active', c.id === 'filter-' + company);
  }});
  render();
}}

// ── 이미지 fallback ──
function imgOrPlaceholder(thumb, title) {{
  if (!thumb) return `<div class="no-img">🎫</div>`;
  return `<img src="${{thumb}}" alt="${{title}}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
          <div class="no-img" style="display:none">🎫</div>`;
}}

// ── 카드 렌더링 ──
function render() {{
  const q = document.getElementById('search').value.trim().toLowerCase();
  const grid = document.getElementById('grid');
  const empty = document.getElementById('empty');

  const filtered = DATA.filter(e => {{
    if (activeCompany !== 'all' && e.card_company !== activeCompany) return false;
    if (activeCat !== 'all' && !e.categories.includes(activeCat)) return false;
    if (q && !e.title.toLowerCase().includes(q) && !e.subtitle.toLowerCase().includes(q)) return false;
    return true;
  }});

  document.getElementById('result-count').textContent = filtered.length + '건 표시 중';

  if (filtered.length === 0) {{
    grid.style.display = 'none'; empty.style.display = 'block';
    return;
  }}
  grid.style.display = ''; empty.style.display = 'none';

  grid.innerHTML = filtered.map((e, i) => {{
    const cls = COMPANY_CLASS[e.card_company] || 'other';
    const cats = e.categories.map(c => `<span class="cat">${{c}}</span>`).join('');
    const likeHtml = e.like_count > 0 ? `<div class="ev-like">♥ ${{e.like_count}}</div>` : '';
    const dateHtml = e.date_range ? `<div class="ev-date">📅 ${{e.date_range}}</div>` : '';
    const subHtml = e.subtitle ? `<div class="ev-subtitle">${{e.subtitle}}</div>` : '';
    return `
      <div class="event-card" onclick="openModal(${{i}}, ${{JSON.stringify(filtered.map(x=>x.event_id)).replace(/'/g,'')}})" data-idx="${{i}}">
        <div class="thumb">
          ${{imgOrPlaceholder(e.thumbnail, e.title)}}
          <div class="company-badge ${{cls}}">${{e.card_company}}</div>
        </div>
        <div class="body">
          <div class="ev-title">${{e.title}}</div>
          ${{subHtml}}
          <div class="ev-cats">${{cats}}</div>
          ${{dateHtml}}
          ${{likeHtml}}
        </div>
      </div>`;
  }}).join('');

  // 클릭 이벤트 재등록
  grid.querySelectorAll('.event-card').forEach((card, i) => {{
    card.onclick = () => openModalByEvent(filtered[i]);
  }});
}}

function openModalByEvent(e) {{
  const modal = document.getElementById('modal');
  const img = document.getElementById('modal-img');
  if (e.thumbnail) {{
    img.src = e.thumbnail; img.style.display = 'block';
    img.onerror = () => {{ img.style.display = 'none'; }};
  }} else {{ img.style.display = 'none'; }}

  const cls = COMPANY_CLASS[e.card_company] || 'other';
  document.getElementById('modal-company').innerHTML =
    `<span class="company-badge ${{cls}}" style="padding:4px 10px;border-radius:6px;font-size:.8rem">${{e.card_company}}</span>`;
  document.getElementById('modal-title').textContent = e.title;
  document.getElementById('modal-sub').textContent = e.subtitle || '';
  document.getElementById('modal-date').innerHTML = e.date_range
    ? `📅 <strong>${{e.date_range}}</strong>` : '';
  document.getElementById('modal-cats').innerHTML =
    e.categories.map(c => `<span class="cat">${{c}}</span>`).join('');

  const link = document.getElementById('modal-link');
  if (e.url) {{
    link.href = e.url; link.style.display = 'block';
  }} else {{ link.style.display = 'none'; }}

  modal.classList.add('open');
  document.body.style.overflow = 'hidden';
}}

function closeModal(ev) {{
  if (ev.target === document.getElementById('modal')) closeModalDirect();
}}
function closeModalDirect() {{
  document.getElementById('modal').classList.remove('open');
  document.body.style.overflow = '';
}}
document.addEventListener('keydown', e => {{ if (e.key === 'Escape') closeModalDirect(); }});

// ── 초기화 ──
initCounts();
initCatFilters();
render();
</script>
</body>
</html>"""

out_path = os.path.join(os.path.dirname(__file__), "viewer.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n✅ 뷰어 생성 완료: viewer.html")
print(f"   브라우저에서 직접 열기: {out_path}")
