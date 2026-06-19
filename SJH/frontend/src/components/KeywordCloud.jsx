import React, { useMemo } from 'react'
import './KeywordCloud.css'

// ── 색상 팔레트 ─────────────────────────────────────────────────────────────
const MEME_COLORS  = ['#f59e0b', '#fbbf24', '#fb923c', '#f472b6', '#a78bfa', '#34d399', '#60a5fa', '#f87171']
const CARD_COLORS  = ['#00d4ff', '#38bdf8', '#93c5fd', '#67e8f9', '#6ee7b7', '#86efac', '#a5f3fc', '#bae6fd']

// ── 카드 이벤트 타이틀 불용어 ────────────────────────────────────────────────
const TITLE_STOPWORDS = new Set([
  '이용', '적용', '혜택', '할인', '카드', '이벤트', '최대', '이상', '결제',
  '캐시백', '및', '적립', '통해', '프로모션', '한정', '바로', '기간', '제공',
  '서비스', '월', '년', '일', '까지', '포인트', '마일리지', '무이자', '할부',
  '전월', '실적', '조건', '신청', '가능', '대상', '고객', '추가', '사용',
  'kb', 'KB', '이용', '회원', '경우', '가입', '발급', '신규', '선착순',
  '추첨', '특별', '한도', '기본', '최소', '제외', '내', '등', '또는',
  '부터', '해당', '오늘', '지금', '매월', '매일', '무료', '자동', '완료',
])

// ── 카드 이벤트 키워드 추출 ──────────────────────────────────────────────────
function extractCardKeywords(cardEvents) {
  const freq = {}

  // by_category: 카테고리 이름을 높은 가중치로 추가
  for (const cat of (cardEvents?.by_category || [])) {
    if (cat.category && cat.category.length >= 2) {
      freq[cat.category] = (freq[cat.category] || 0) + cat.count * 3
    }
  }

  // events[].title: 토큰화 후 빈도 카운트
  for (const ev of (cardEvents?.events || []).slice(0, 200)) {
    const tokens = (ev.title || '').split(/[\s\-\/·!~+&,.()\[\]:%]+/)
    for (const token of tokens) {
      const t = token.trim()
      if (
        t.length >= 2 &&
        !TITLE_STOPWORDS.has(t) &&
        !/^\d+(%|만원|원|개|회|배)?$/.test(t)
      ) {
        freq[t] = (freq[t] || 0) + 1
      }
    }
  }

  return Object.entries(freq)
    .map(([text, value]) => ({ text, value, type: 'card' }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 40)
}

// ── 밈/트렌드 키워드 추출 ────────────────────────────────────────────────────
function extractMemeKeywords(youtubeTrends) {
  return (youtubeTrends?.trends || [])
    .filter(t => t.keyword && (t.meme_score > 0 || t.trend_score > 0))
    .map(t => ({
      text: t.keyword,
      value: t.meme_score || t.trend_score || 1,
      type: 'meme',
    }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 25)
}

// ── Archimedean spiral 배치 알고리즘 ─────────────────────────────────────────
// 큰 단어부터 중심에 배치, 타원 영역 안에서 overlap 없이 나선형으로 탐색
const GOLDEN_ANGLE = 2.39996322972  // 2π / φ²

function placeWords(words, W, H) {
  if (!words.length) return []

  const cx = W / 2
  const cy = H / 2
  const ra = W * 0.455   // 수평 타원 반경
  const rb = H * 0.440   // 수직 타원 반경

  const maxVal = Math.max(...words.map(w => w.value), 1)
  const minVal = Math.min(...words.map(w => w.value), 0)
  const range = maxVal - minVal || 1

  const placed = []

  for (let i = 0; i < words.length; i++) {
    const word = words[i]
    const normalized = (word.value - minVal) / range
    const fontSize = Math.round(13 + normalized * 33)  // 13~46px
    const estW = word.text.length * fontSize * 0.65
    const estH = fontSize * 1.35

    let angle = i * GOLDEN_ANGLE
    let spiralStep = 0
    let px = cx - estW / 2
    let py = cy - estH / 2
    let found = false

    for (let t = 0; t < 1000; t++) {
      const r = spiralStep * 0.55
      const x = cx + r * Math.cos(angle) - estW / 2
      const y = cy + r * Math.sin(angle) - estH / 2

      // 단어 중심이 타원 안에 있는지 확인
      const wCx = x + estW / 2
      const wCy = y + estH / 2
      const ex = (wCx - cx) / ra
      const ey = (wCy - cy) / rb
      const inEllipse = ex * ex + ey * ey <= 0.87

      if (inEllipse) {
        const noOverlap = placed.every(
          p =>
            x > p.x + p.w + 4 ||
            x + estW < p.x - 4 ||
            y > p.y + p.h + 3 ||
            y + estH < p.y - 3
        )
        if (noOverlap) {
          px = x
          py = y
          found = true
          break
        }
      }

      angle += 0.18
      spiralStep += 0.7
    }

    if (found) {
      placed.push({ ...word, x: px, y: py, w: estW, h: estH, fontSize })
    }
  }

  return placed
}

// ── 컴포넌트 ─────────────────────────────────────────────────────────────────
export default function KeywordCloud({ cardEvents, youtubeTrends }) {
  const W = 540
  const H = 370

  const cardWords = useMemo(() => extractCardKeywords(cardEvents),  [cardEvents])
  const memeWords = useMemo(() => extractMemeKeywords(youtubeTrends), [youtubeTrends])

  // 밈 키워드를 앞에 배치해 중심부에 오도록, 전체 value 기준 내림차순 정렬
  const allWords = useMemo(
    () => [...memeWords, ...cardWords].sort((a, b) => b.value - a.value),
    [cardWords, memeWords]
  )

  const positioned = useMemo(() => placeWords(allWords, W, H), [allWords])

  if (positioned.length === 0) {
    return <p className="empty-text">키워드 데이터를 수집 중입니다...</p>
  }

  return (
    <div className="keyword-cloud-wrapper">
      <div
        className="keyword-cloud-canvas"
        style={{ width: W, height: H, position: 'relative' }}
      >
        {positioned.map((w, i) => {
          const palette = w.type === 'meme' ? MEME_COLORS : CARD_COLORS
          const color = palette[i % palette.length]
          return (
            <span
              key={`${w.text}-${i}`}
              className="cloud-word"
              style={{
                position: 'absolute',
                left: Math.round(w.x),
                top:  Math.round(w.y),
                fontSize: w.fontSize,
                color,
                fontWeight: w.fontSize >= 22 ? 700 : 400,
                lineHeight: 1.2,
                whiteSpace: 'nowrap',
                cursor: 'default',
              }}
              title={`${w.text} (${w.type === 'meme' ? '밈점수' : '빈도'}: ${Math.round(w.value)})`}
            >
              {w.text}
            </span>
          )
        })}
      </div>

      <div className="cloud-legend">
        <span className="legend-meme">■ 밈/트렌드</span>
        <span className="legend-card">■ 카드 이벤트</span>
      </div>
    </div>
  )
}
