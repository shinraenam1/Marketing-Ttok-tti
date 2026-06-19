import './AnalysisPanel.css'

function AnalysisPanel({ analysis, cardEvents, youtubeTrends }) {
  return (
    <div className="analysis-panel">
      <div className="analysis-content">
        <div className="markdown-body">
          {analysis ? (
            analysis.split('\n').map((line, idx) => {
              if (line.startsWith('##')) {
                return <h3 key={idx}>{line.replace('##', '').trim()}</h3>
              } else if (line.startsWith('**')) {
                return <strong key={idx}>{line.replace(/\*\*/g, '')}</strong>
              } else if (line.trim()) {
                return <p key={idx}>{line}</p>
              }
              return null
            })
          ) : (
            <p>분석 결과를 로드 중입니다...</p>
          )}
        </div>

        {cardEvents && (
          <div className="data-summary">
            <h4>📍 카드사 이벤트</h4>
            <pre>{JSON.stringify(cardEvents, null, 2)}</pre>
          </div>
        )}

        {youtubeTrends && (
          <div className="data-summary">
            <h4>📺 YouTube 트렌드</h4>
            <pre>{JSON.stringify(youtubeTrends, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  )
}

export default AnalysisPanel
