import React from 'react'
import './KeywordAnalysisPanel.css'

export default function KeywordAnalysisPanel({ 
  memeKeywords = [], 
  cardKeywords = [], 
  memeExplanation = '', 
  cardExplanation = '',
  memeKeywordExplanations = {},
  cardKeywordExplanations = {}
}) {
  return (
    <div className="keyword-analysis-grid">
      {/* 좌측: 밈/트렌드 */}
      <div className="keyword-column meme-column">
        <h4>☒ 소셜 급등 키워드 (TOP 10)</h4>
        <div className="keyword-list">
          {memeKeywords.slice(0, 10).map((kw, idx) => {
            // API 호출로 받은 설명만 사용
            const explanation = memeKeywordExplanations[kw.keyword];
            
            return (
              <div key={idx} className="keyword-item">
                <div className="keyword-content">
                  <span className="keyword-rank">{idx + 1}.</span>
                  <span className="keyword-text">{kw.keyword}</span>
                  <span className="keyword-score">점수 {Math.round(kw.meme_score || kw.trend_score || 0)}</span>
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
        <div className="keyword-list">
          {cardKeywords.slice(0, 10).map((kw, idx) => {
            // API 호출로 받은 설명만 사용
            const explanation = cardKeywordExplanations[kw.category];
            
            return (
              <div key={idx} className="keyword-item">
                <div className="keyword-content">
                  <span className="keyword-rank">{idx + 1}.</span>
                  <span className="keyword-text">{kw.category}</span>
                  <span className="keyword-count">{kw.count}건</span>
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
