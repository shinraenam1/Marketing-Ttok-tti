import './AnalysisPanel.css'

function AnalysisPanel({ analysisSummary, cardEvents, youtubeTrends }) {
  const memeItems = Array.isArray(youtubeTrends?.trends)
    ? youtubeTrends.trends.slice(0, 5)
    : []

  const categoryItems = Array.isArray(cardEvents?.by_category)
    ? cardEvents.by_category.slice(0, 5)
    : []

  const fallbackSummary = '최다 이벤트 카테고리와 상위 밈 키워드를 결합한 메시지 중심 프로모션을 우선 실행하는 전략을 추천합니다.'
  const summaryText = analysisSummary || fallbackSummary

  return (
    <div className="analysis-panel">
      <div className="analysis-header">
        <h3>📊 [1-2단계] 정기 트렌드 & 타사 동향 리포트 (08:00 AM 실행 완료)</h3>
      </div>

      <div className="insight-grid">
        <div className="insight-card">
          <h4>☒ 소셜 급등 키워드</h4>
          {memeItems.length === 0 ? (
            <p className="empty-text">밈 데이터 수집 중입니다.</p>
          ) : (
            <ol className="rank-list">
              {memeItems.map((item, index) => (
                <li key={`${item.keyword}-${index}`}>
                  <span className="item-title">{item.keyword}</span>
                  <span className="item-meta">점수 {Math.round(item.meme_score)} / 성장률 {Math.round(item.growth_rate_pct)}%</span>
                </li>
              ))}
            </ol>
          )}
        </div>

        <div className="insight-card">
          <h4>☒ 카드사 카테고리 이벤트 TOP</h4>
          {categoryItems.length === 0 ? (
            <p className="empty-text">카테고리 집계 데이터가 없습니다.</p>
          ) : (
            <ul className="category-list">
              {categoryItems.map((item, index) => (
                <li key={`${item.category}-${index}`}>
                  <span className="item-title">{item.category}</span>
                  <span className="item-badge">{item.count}건</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="insight-section">
        <h4>💡 [AI 마케터 분석 한줄 요약]</h4>
        <p className="insight-text">{summaryText}</p>
      </div>
    </div>
  )
}

export default AnalysisPanel
