import React, { useMemo } from 'react'
import './KeywordCloud.css'

const CARD_COLORS = ['#00d4ff', '#38bdf8', '#93c5fd', '#67e8f9', '#6ee7b7', '#86efac', '#a5f3fc', '#bae6fd']
const GOLDEN_ANGLE = 2.39996322972

const TITLE_STOPWORDS = new Set([
  '이용', '적용', '혜택', '할인', '카드', '이벤트', '최대', '이상', '결제',
  '캐시백', '및', '적립', '통해', '프로모션', '한정', '바로', '기간', '제공',
  '서비스', '월', '년', '일', '까지', '포인트', '마일리지', '무이자', '할부',
  '전월', '실적', '조건', '신청', '가능', '대상', '고객', '추가', '사용',
  'kb', 'KB', '이용', '회원', '경우', '가입', '발급', '신규', '선착순',
  '추첨', '특별', '한도', '기본', '최소', '제외', '내', '등', '또는',
  '부터', '해당', '오늘', '지금', '매월', '매일', '무료', '자동', '완료',
])

function placeWords(words, W, H) {
  if (!words.length) return []

  const cx = W / 2
  const cy = H / 2
  const ra = W * 0.455
  const rb = H * 0.440

  const maxVal = Math.max(...words.map(w => w.value), 1)
  const minVal = Math.min(...words.map(w => w.value), 0)
  const range = maxVal - minVal || 1

  const placed = []

  for (let i = 0; i < words.length; i++) {
    const word = words[i]
    const normalized = (word.value - minVal) / range
    const fontSize = Math.round(13 + normalized * 33)
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

export default function CardKeywordCloud({ cardEvents }) {
  const W = 260
  const H = 240

  const cardWords = useMemo(() => {
    const freq = {}

    for (const cat of (cardEvents?.by_category || [])) {
      if (cat.category && cat.category.length >= 2) {
        freq[cat.category] = (freq[cat.category] || 0) + cat.count * 3
      }
    }

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
      .slice(0, 20)
  }, [cardEvents])

  const positioned = useMemo(() => placeWords(cardWords, W, H), [cardWords])

  if (positioned.length === 0) {
    return <p className="empty-text">카드 데이터 수집 중...</p>
  }

  return (
    <div className="keyword-cloud-wrapper">
      <div
        className="keyword-cloud-canvas"
        style={{ width: W, height: H, position: 'relative' }}
      >
        {positioned.map((w, i) => {
          const color = CARD_COLORS[i % CARD_COLORS.length]
          return (
            <span
              key={`${w.text}-${i}`}
              className="cloud-word"
              style={{
                position: 'absolute',
                left: Math.round(w.x),
                top: Math.round(w.y),
                fontSize: w.fontSize,
                color,
                fontWeight: w.fontSize >= 22 ? 700 : 400,
                lineHeight: 1.2,
                whiteSpace: 'nowrap',
                cursor: 'default',
              }}
              title={`${w.text} (빈도: ${Math.round(w.value)})`}
            >
              {w.text}
            </span>
          )
        })}
      </div>
    </div>
  )
}
