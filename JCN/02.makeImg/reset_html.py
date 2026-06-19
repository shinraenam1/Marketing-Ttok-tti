target = r"c:\Users\CNJUNG\Documents\2026_hackathon\20260619\02.makeImg\templates\index.html"

html = """\
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>BNK 부산은행 AI 광고 이미지 생성기</title>
  <style>
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    :root{
      --red:#C8102E;--red-dark:#9B0B22;--gray:#54534A;--gray-lt:#8a8980;
      --bg:#f7f6f4;--card:#ffffff;--border:#e2e0db;--text:#1a1a18;--text-sub:#6b6a62;
    }
    body{font-family:'Apple SD Gothic Neo','Noto Sans KR','Segoe UI',sans-serif;
         background:var(--bg);color:var(--text);min-height:100vh;
         display:flex;flex-direction:column;align-items:center;padding:0 0 60px}
    .header{width:100%;background:var(--red);padding:0 40px;
            display:flex;align-items:center;justify-content:space-between;height:64px;
            box-shadow:0 2px 8px rgba(200,16,46,.25)}
    .header-brand{display:flex;align-items:center;gap:14px}
    .hb-title{font-size:1.35rem;font-weight:800;color:#fff;letter-spacing:-.02em}
    .hb-title span{font-weight:400;opacity:.85}
    .hb-tag{font-size:.72rem;color:rgba(255,255,255,.7);background:rgba(255,255,255,.15);
            border-radius:20px;padding:3px 10px;letter-spacing:.03em}
    .subhdr{width:100%;background:var(--gray);padding:10px 40px;
            display:flex;align-items:center;gap:8px}
    .subhdr-dot{width:6px;height:6px;background:var(--red);border-radius:50%;flex-shrink:0}
    .subhdr p{font-size:.8rem;color:rgba(255,255,255,.75)}
    .main{display:flex;gap:28px;width:100%;max-width:1160px;padding:36px 24px 0;align-items:flex-start}
    .panel{flex:0 0 360px;background:var(--card);border:1px solid var(--border);
           border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.07)}
    .ph{background:var(--red);padding:16px 22px;display:flex;align-items:center;gap:10px}
    .ph h2{font-size:.95rem;font-weight:700;color:#fff;letter-spacing:.02em}
    .pb{padding:22px}
    .field{margin-bottom:16px}
    .field label{display:flex;align-items:center;gap:6px;font-size:.78rem;font-weight:700;
                 color:var(--gray);margin-bottom:6px;text-transform:uppercase;letter-spacing:.04em}
    .req{font-size:.68rem;background:var(--red);color:#fff;border-radius:3px;
         padding:1px 5px;font-weight:600;letter-spacing:0;text-transform:none}
    .opt{font-size:.68rem;color:var(--gray-lt);font-weight:400;text-transform:none;letter-spacing:0}
    .field input,.field textarea{width:100%;background:#fafaf8;border:1.5px solid var(--border);
      border-radius:7px;color:var(--text);font-size:.9rem;padding:9px 13px;
      transition:border-color .2s,box-shadow .2s;outline:none;resize:vertical;font-family:inherit}
    .field input:focus,.field textarea:focus{border-color:var(--red);box-shadow:0 0 0 3px rgba(200,16,46,.1)}
    .field input::placeholder,.field textarea::placeholder{color:#bbb9b0}
    .divider{border:none;border-top:1px solid var(--border);margin:18px 0}
    .plat-grp{display:flex;gap:8px}
    .plat-grp label{flex:1;cursor:pointer}
    .plat-grp input[type=radio]{display:none}
    .plat-btn{display:block;text-align:center;padding:10px 4px;border-radius:7px;
              border:1.5px solid var(--border);font-size:.75rem;color:var(--gray-lt);
              transition:all .2s;user-select:none;background:#fafaf8;line-height:1.4}
    .plat-btn strong{display:block;font-size:.82rem;color:var(--text)}
    .plat-grp input[type=radio]:checked+.plat-btn{border-color:var(--red);background:#fff5f6;color:var(--red)}
    .plat-grp input[type=radio]:checked+.plat-btn strong{color:var(--red)}
    .pos-grp{display:grid;grid-template-columns:1fr 1fr;gap:6px}
    .pos-grp label{cursor:pointer}
    .pos-grp input[type=radio]{display:none}
    .pos-btn{display:block;text-align:center;padding:7px 4px;border-radius:6px;
             border:1.5px solid var(--border);font-size:.75rem;color:var(--gray-lt);
             transition:all .2s;user-select:none;background:#fafaf8}
    .pos-grp input[type=radio]:checked+.pos-btn{border-color:var(--gray);background:#f0efeb;
             color:var(--gray);font-weight:600}
    .btn-gen{width:100%;padding:14px;border-radius:8px;border:none;background:var(--red);
             color:#fff;font-size:1rem;font-weight:700;cursor:pointer;margin-top:6px;
             transition:background .2s,transform .1s;letter-spacing:.03em;font-family:inherit}
    .btn-gen:hover{background:var(--red-dark)}
    .btn-gen:active{transform:scale(.98)}
    .btn-gen:disabled{opacity:.45;cursor:not-allowed}
    .hint{text-align:center;font-size:.7rem;color:var(--gray-lt);margin-top:8px}
    .result{flex:1;background:var(--card);border:1px solid var(--border);border-radius:12px;
            overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.07);min-height:520px;
            display:flex;flex-direction:column}
    .rh{background:var(--gray);padding:16px 22px;display:flex;align-items:center;gap:10px}
    .rh h2{font-size:.95rem;font-weight:700;color:#fff;letter-spacing:.02em}
    .rb{padding:24px;flex:1;display:flex;flex-direction:column}
    .ph-empty{flex:1;display:flex;flex-direction:column;align-items:center;
              justify-content:center;gap:14px;color:#ccc8c0}
    .ph-icon{width:72px;height:72px;border:2px dashed #ddd8d0;border-radius:12px;
             display:flex;align-items:center;justify-content:center}
    .ph-empty p{font-size:.88rem}
    .loader{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px}
    .spinner{width:44px;height:44px;border:4px solid var(--border);border-top-color:var(--red);
             border-radius:50%;animation:spin .85s linear infinite}
    @keyframes spin{to{transform:rotate(360deg)}}
    .loader-txt{color:var(--gray-lt);font-size:.88rem}
    .res-wrap{flex:1;display:flex;flex-direction:column;gap:14px}
    .res-wrap img{width:100%;border-radius:8px;border:1px solid var(--border)}
    .res-meta{display:flex;align-items:center;gap:16px;font-size:.75rem;color:var(--gray-lt)}
    .meta-pill{background:#f0efeb;border-radius:20px;padding:3px 10px;color:var(--gray);font-weight:600}
    .res-actions{display:flex;gap:10px}
    .btn-dl{padding:9px 20px;border-radius:7px;border:1.5px solid var(--red);background:transparent;
            color:var(--red);font-size:.85rem;font-weight:600;cursor:pointer;
            transition:background .2s;font-family:inherit}
    .btn-dl:hover{background:#fff5f6}
    .err-box{background:#fff5f6;border:1px solid #fca5a5;border-radius:8px;
             padding:14px 16px;color:#b91c1c;font-size:.85rem}
    details{margin-top:4px}
    summary{cursor:pointer;font-size:.75rem;color:var(--gray-lt);list-style:none;user-select:none}
    summary:hover{color:var(--gray)}
    .prompt-txt{margin-top:8px;padding:10px 12px;background:#f7f6f4;border-radius:6px;
                font-size:.72rem;color:#888;white-space:pre-wrap;line-height:1.6}
    @media(max-width:780px){.main{flex-direction:column}.panel{flex:none;width:100%}}
  </style>
</head>
<body>

<header class="header">
  <div class="header-brand">
    <div class="hb-title">BNK <span>부산은행</span></div>
    <span class="hb-tag">AI 광고 이미지 생성기</span>
  </div>
  <span style="font-size:.75rem;color:rgba(255,255,255,.5)">GPT-IMAGE-2 · Azure AI Foundry</span>
</header>

<div class="subhdr">
  <div class="subhdr-dot"></div>
  <p>상품 정보를 입력하면 BNK 부산은행 브랜드 가이드에 맞는 금융 광고 이미지를 자동으로 생성합니다.</p>
</div>

<div class="main">

  <!-- 입력 패널 -->
  <div class="panel">
    <div class="ph">
      <svg width="16" height="16" fill="none" stroke="#fff" stroke-width="2" viewBox="0 0 24 24">
        <path d="M12 20h9M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/>
      </svg>
      <h2>광고 인풋 설정</h2>
    </div>
    <div class="pb">

      <div class="field">
        <label>상품종류 <span class="req">필수</span></label>
        <input id="inp-product" type="text" placeholder="예) BNK 프리미엄 적금카드" />
      </div>

      <div class="field">
        <label>상품 혜택 <span class="req">필수</span></label>
        <input id="inp-benefit" type="text" placeholder="예) 연 5% 금리, 연회비 영구 무료" />
      </div>

      <div class="field">
        <label>광고 컨셉 <span class="opt">(선택)</span></label>
        <textarea id="inp-concept" rows="2" placeholder="예) 여름 특별 혜택, 신뢰와 성장의 파트너"></textarea>
      </div>

      <hr class="divider" />

      <div class="field">
        <label>플랫폼 / 해상도</label>
        <div class="plat-grp">
          <label><input type="radio" name="platform" value="sns" checked /><span class="plat-btn"><strong>SNS</strong>816×816</span></label>
          <label><input type="radio" name="platform" value="blog" /><span class="plat-btn"><strong>블로그</strong>1024×640</span></label>
          <label><input type="radio" name="platform" value="banner" /><span class="plat-btn"><strong>홈페이지</strong>1440×480</span></label>
        </div>
      </div>

      <div class="field">
        <label>로고 위치</label>
        <div class="pos-grp">
          <label><input type="radio" name="logo_pos" value="bottom-left" checked /><span class="pos-btn">↙ 좌하단</span></label>
          <label><input type="radio" name="logo_pos" value="bottom-right" /><span class="pos-btn">↘ 우하단</span></label>
          <label><input type="radio" name="logo_pos" value="top-left" /><span class="pos-btn">↖ 좌상단</span></label>
          <label><input type="radio" name="logo_pos" value="top-right" /><span class="pos-btn">↗ 우상단</span></label>
        </div>
      </div>

      <button class="btn-gen" id="btnGen" onclick="doGenerate()">▶ &nbsp;이미지 생성</button>
      <p class="hint">Ctrl + Enter 로도 실행 가능</p>
    </div>
  </div>

  <!-- 결과 패널 -->
  <div class="result">
    <div class="rh">
      <svg width="16" height="16" fill="none" stroke="#fff" stroke-width="2" viewBox="0 0 24 24">
        <rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8.5" cy="8.5" r="1.5"/>
        <path d="M21 15l-5-5L5 21"/>
      </svg>
      <h2>생성 결과</h2>
    </div>
    <div class="rb" id="resultBody">
      <div class="ph-empty">
        <div class="ph-icon">
          <svg width="32" height="32" fill="none" stroke="currentColor" stroke-width="1.3" viewBox="0 0 24 24">
            <rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8.5" cy="8.5" r="1.5"/>
            <path d="M21 15l-5-5L5 21"/>
          </svg>
        </div>
        <p>상품 정보를 입력하고 이미지를 생성해보세요</p>
        <p style="font-size:.75rem;color:#ddd8d0">BNK 부산은행 로고가 자동으로 합성됩니다</p>
      </div>
    </div>
  </div>

</div>

<script>
async function doGenerate() {
  const product  = document.getElementById('inp-product').value.trim();
  const benefit  = document.getElementById('inp-benefit').value.trim();
  const concept  = document.getElementById('inp-concept').value.trim();
  const platform = document.querySelector('input[name=platform]:checked').value;
  const logo_pos = document.querySelector('input[name=logo_pos]:checked').value;

  if (!product || !benefit) { alert('상품종류와 혜택은 필수 입력입니다.'); return; }

  const btn = document.getElementById('btnGen');
  btn.disabled = true; btn.textContent = '생성 중...';

  document.getElementById('resultBody').innerHTML =
    '<div class="loader"><div class="spinner"></div>' +
    '<div class="loader-txt">GPT-IMAGE-2 가 이미지를 생성하는 중입니다…</div></div>';

  try {
    const res  = await fetch('/generate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({product, benefit, concept, platform, logo_pos})
    });
    const data = await res.json();

    if (!res.ok || data.error) {
      document.getElementById('resultBody').innerHTML =
        '<div class="err-box">오류: ' + (data.error || '알 수 없는 오류') + '</div>';
      return;
    }

    const imgSrc = 'data:image/png;base64,' + data.image;
    const fname  = 'bnk_' + platform + '_' + Date.now() + '.png';
    document.getElementById('resultBody').innerHTML =
      '<div class="res-wrap">' +
        '<img src="' + imgSrc + '" alt="BNK 부산은행 광고 이미지" />' +
        '<div class="res-meta"><span class="meta-pill">' + platform.toUpperCase() + '</span>' +
          '<span>' + data.size + '</span><span>로고 합성 완료</span></div>' +
        '<div class="res-actions">' +
          '<button class="btn-dl" id="btnDl">↓ 이미지 다운로드</button>' +
        '</div>' +
        '<details><summary>프롬프트 보기</summary>' +
          '<div class="prompt-txt">' + data.prompt.replace(/</g,'&lt;') + '</div>' +
        '</details>' +
      '</div>';
    document.getElementById('btnDl').addEventListener('click', function() {
      dlImg(imgSrc, fname);
    });
  } catch(e) {
    document.getElementById('resultBody').innerHTML =
      '<div class="err-box">네트워크 오류: ' + e.message + '</div>';
  } finally {
    btn.disabled = false; btn.textContent = '▶  이미지 생성';
  }
}

function dlImg(src, fname) {
  const a = document.createElement('a'); a.href = src; a.download = fname; a.click();
}

document.addEventListener('keydown', e => { if(e.key==='Enter' && e.ctrlKey) doGenerate(); });
</script>

</body>
</html>
"""

with open(target, 'w', encoding='utf-8') as f:
    f.write(html)

# 검증
with open(target, encoding='utf-8') as f:
    content = f.read()

doctype_count = content.count('<!DOCTYPE')
body_count    = content.count('<body')
html_count    = content.count('</html>')
print(f'DOCTYPE: {doctype_count}, <body>: {body_count}, </html>: {html_count}')
print(f'파일 크기: {len(content)} bytes')
print('OK' if doctype_count == 1 and body_count == 1 and html_count == 1 else 'ERROR: 중복 발견')
