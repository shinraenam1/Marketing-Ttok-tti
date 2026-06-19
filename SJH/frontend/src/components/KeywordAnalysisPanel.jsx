import React from 'react'
import './KeywordAnalysisPanel.css'

export default function KeywordAnalysisPanel({ 
  memeKeywords = [], 
  cardKeywords = [], 
  memeExplanation = '', 
  cardExplanation = '',
  memeKeywordExplanations = {},
  cardKeywordExplanations = {},
  selectedMemeKeyword = null,
  selectedCardKeyword = null,
  onMemeSelect,
  onCardSelect
}) {
  return (
    <div className="keyword-analysis-grid">
      {/* 좌측: 밈/트렌드 */}
      <div className="keyword-column meme-column">
        <h4>☒ 소셜 급등 키워드 (TOP 10)</h4>
        {onMemeSelect && <p className="select-hint">키워드를 클릭하면 Step 3-4에 반영됩니다</p>}
        <div className="keyword-list">
          {memeKeywords.slice(0, 10).map((kw, idx) => {
            const explanation = memeKeywordExplanations[kw.keyword];
            const isSelected = selectedMemeKeyword?.keyword === kw.keyword;

            return (
              <div
                key={idx}
                className={`keyword-item${isSelected ? ' keyword-selected' : ''}${onMemeSelect ? ' keyword-clickable' : ''}`}
                onClick={() => onMemeSelect && onMemeSelect({ keyword: kw.keyword, explanation: explanation || '' })}
              >
                <div className="keyword-content">
                  <span className="keyword-rank">{idx + 1}.</span>
                  <span className="keyword-text">{kw.keyword}</span>
                  <span className="keyword-score">점수 {Math.round(kw.meme_score || kw.trend_score || 0)}</span>
                  {isSelected && <span className="selected-badge">✓ 선택됨</span>}
                </div>
                {explanation && (
                  <div className="keyword-reason">{explanation}</div>
                )}
              </div>
            )
          })}
        </div>
        {memeExplanation && (
          <div className="explanation-box meme-explanation">
            <p>{memeExplanation}</p>
          </div>
        )}
      </div>

      {/* 우측: 카드 이벤트 */}
      <div className="keyword-column card-column">
        <h4>☒ 카드사 카테고리 이벤트 (TOP 10)</h4>
        {onCardSelect && <p className="select-hint">카테고리를 클릭하면 Step 3-4에 반영됩니다</p>}
        <div className="keyword-list">
          {cardKeywords.slice(0, 10).map((kw, idx) => {
            const explanation = cardKeywordExplanations[kw.category];
            const isSelected = selectedCardKeyword?.category === kw.category;

            return (
              <div
                key={idx}
                className={`keyword-item${isSelected ? ' keyword-selected' : ''}${onCardSelect ? ' keyword-clickable' : ''}`}
                onClick={() => onCardSelect && onCardSelect({ category: kw.category, explanation: explanation || '' })}
              >
                <div className="keyword-content">
                  <span className="keyword-rank">{idx + 1}.</span>
                  <span className="keyword-text">{kw.category}</span>
                  <span className="keyword-count">{kw.count}건</span>
                  {isSelected && <span className="selected-badge">✓ 선택됨</span>}
                </div>
                {explanation && (
                  <div className="keyword-reason">{explanation}</div>
                )}
              </div>
            )
          })}
        </div>
        {cardExplanation && (
          <div className="explanation-box card-explanation">
            <p>{cardExplanation}</p>
          </div>
        )}
      </div>
    </div>
  )
}
