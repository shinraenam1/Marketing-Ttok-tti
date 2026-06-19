import React, { useMemo } from 'react'
import './KeywordCloud.css'

const MEME_COLORS = ['#f59e0b', '#fbbf24', '#fb923c', '#f472b6', '#a78bfa', '#34d399', '#60a5fa', '#f87171']
const GOLDEN_ANGLE = 2.39996322972

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

export default function MemeKeywordCloud({ youtubeTrends }) {
  const W = 260
  const H = 240

  const memeWords = useMemo(() => {
    return (youtubeTrends?.trends || [])
      .filter(t => t.keyword && (t.meme_score > 0 || t.trend_score > 0))
      .map((t, idx) => ({
        text: t.keyword,
        value: t.meme_score || t.trend_score || 1,
        type: 'meme',
        index: idx
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 20)
  }, [youtubeTrends])

  const positioned = useMemo(() => placeWords(memeWords, W, H), [memeWords])

  if (positioned.length === 0) {
    return <p className="empty-text">밈 데이터 수집 중...</p>
  }

  return (
    <div className="keyword-cloud-wrapper">
      <div
        className="keyword-cloud-canvas"
        style={{ width: W, height: H, position: 'relative' }}
      >
        {positioned.map((w, i) => {
          const color = MEME_COLORS[i % MEME_COLORS.length]
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
              title={`${w.text} (점수: ${Math.round(w.value)})`}
            >
              {w.text}
            </span>
          )
        })}
      </div>
    </div>
  )
}
