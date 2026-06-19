import React from 'react'
import MemeKeywordCloud from './MemeKeywordCloud'
import CardKeywordCloud from './CardKeywordCloud'
import KeywordAnalysisPanel from './KeywordAnalysisPanel'
import './AnalysisPanel.css'

function AnalysisPanel({ 
  analysisSummary, 
  cardEvents, 
  youtubeTrends,
  memeExplanation = '',
  cardExplanation = '',
  memeKeywordExplanations = {},
  cardKeywordExplanations = {}
}) {
  const topMemeTrends = Array.isArray(youtubeTrends?.trends)
    ? [...youtubeTrends.trends]
        .sort((a, b) => Number(b?.meme_score || 0) - Number(a?.meme_score || 0))
        .slice(0, 10)
    : []

  const topCardCategories = Array.isArray(cardEvents?.by_category)
    ? [...cardEvents.by_category]
        .sort((a, b) => Number(b?.count || 0) - Number(a?.count || 0))
        .slice(0, 10)
    : []

  const fallbackSummary = '최다 이벤트 카테고리와 상위 밈 키워드를 결합한 메시지 중심 프로모션을 우선 실행하는 전략을 추천합니다.'
  const summaryText = analysisSummary || fallbackSummary

  return (
    <div className="analysis-panel">
      <div className="analysis-header">
        <h3>📊 [1-2단계] 정기 트렌드 &amp; 타사 동향 리포트 (08:00 AM 실행 완료)</h3>
      </div>

      {/* 키워드 클라우드 - 밈/트렌드 vs 카드 이벤트 */}
      <div className="insight-section cloud-section">
        <h4>☁️ 키워드 클라우드</h4>
        <div className="cloud-grid">
          <div className="cloud-container">
            <h5>밈/트렌드</h5>
            <MemeKeywordCloud youtubeTrends={youtubeTrends} />
          </div>
          <div className="cloud-container">
            <h5>카드 이벤트</h5>
            <CardKeywordCloud cardEvents={cardEvents} />
          </div>
        </div>
      </div>

      {/* 좌/우 키워드 분석 + OpenAI 설명 */}
      <KeywordAnalysisPanel 
        memeKeywords={topMemeTrends}
        cardKeywords={topCardCategories}
        memeExplanation={memeExplanation}
        cardExplanation={cardExplanation}
        memeKeywordExplanations={memeKeywordExplanations}
        cardKeywordExplanations={cardKeywordExplanations}
      />

      {/* 조합 요약 데이터 */}
      <div className="insight-section">
        <h4>💡 [조합 요약 데이터]</h4>
        <div className="summary-list">{summaryText}</div>
      </div>
    </div>
  )
}

export default AnalysisPanel
