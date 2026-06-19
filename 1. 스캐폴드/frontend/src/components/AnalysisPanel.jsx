import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import './AnalysisPanel.css'

function AnalysisPanel({ analysis, cardEvents, youtubeTrends }) {
  // 샘플 데이터 - 실제로는 API 응답에서 받을 데이터
  const trendData = [
    { day: '00일', social: 25, keyword: 15 },
    { day: '07일', social: 60, keyword: 35 },
    { day: '04일', social: 45, keyword: 30 },
    { day: '06일', social: 40, keyword: 25 },
    { day: '08일', social: 35, keyword: 20 },
    { day: '10일', social: 110, keyword: 45 }
  ]

  const dailyData = [
    { day: '1일', value: 250 },
    { day: '2일', value: 600 },
    { day: '3일', value: 700 },
    { day: '4일', value: 550 },
    { day: '5일', value: 700 },
    { day: '6일', value: 1050 }
  ]

  const weekdayData = [
    { day: '20세', value: 120 },
    { day: '1일', value: 130 },
    { day: '2일', value: 80 },
    { day: '3일', value: 150 },
    { day: '4일', value: 200 },
    { day: '15일', value: 300 }
  ]

  return (
    <div className="analysis-panel">
      <div className="analysis-header">
        <h3>📊 [1-2단계] 정기 트렌드 & 타사 동향 리포트 (08:00 AM 실행 완료)</h3>
      </div>

      <div className="analysis-charts">
        {/* 트렌드 라인 차트 */}
        <div className="chart-container chart-trend">
          <h4>📈 소셜 금등 키워드</h4>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#444" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="social" stroke="#00d4ff" strokeWidth={2} name="소셜" />
              <Line type="monotone" dataKey="keyword" stroke="#ff6b6b" strokeWidth={2} name="키워드" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* 일별 바 차트 */}
        <div className="chart-container chart-daily">
          <h4>📊 일별 통계</h4>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={dailyData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#444" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#4a9eff" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* 요일별 바 차트 */}
        <div className="chart-container chart-weekday">
          <h4>📊 요일/연령별 통계</h4>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={weekdayData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#444" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#4a9eff" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* KPI 카드들 */}
      <div className="kpi-section">
        <h4>📈 주요 지표</h4>
        <div className="kpi-cards">
          <div className="kpi-card">
            <span className="kpi-label">소셜 금등 키워드</span>
            <span className="kpi-value">
              고유가 이슈 (기금값 절약) <span className="increase">▲82%</span>
            </span>
          </div>
          <div className="kpi-card">
            <span className="kpi-label">소셜 금등 키워드</span>
            <span className="kpi-value">
              '게치캐치' 며 챙짓지 <span className="decrease">▼45%</span>
            </span>
          </div>
        </div>
      </div>

      {/* 마케팅 인사이트 */}
      <div className="insight-section">
        <h4>💡 [AI 마케터 분석 한줄 요약]</h4>
        <p className="insight-text">
          고유가 불안 심리와 '게치캐치' 밈을 결합한 당장 주유 캐시백 이벤트를 강력 추천합니다.
        </p>
      </div>

      {/* 원본 분석 텍스트 (필요시) */}
      {analysis && (
        <div className="original-analysis">
          <h5>분석 상세</h5>
          <div className="markdown-body">
            {analysis.split('\n').map((line, idx) => {
              if (line.startsWith('##')) {
                return <h3 key={idx}>{line.replace('##', '').trim()}</h3>
              } else if (line.startsWith('**')) {
                return <strong key={idx}>{line.replace(/\*\*/g, '')}</strong>
              } else if (line.trim()) {
                return <p key={idx}>{line}</p>
              }
              return null
            })}
          </div>
        </div>
      )}

      {cardEvents && (
        <div className="data-summary" style={{ display: 'none' }}>
          <h4>📍 카드사 이벤트</h4>
          <pre>{JSON.stringify(cardEvents, null, 2)}</pre>
        </div>
      )}

      {youtubeTrends && (
        <div className="data-summary" style={{ display: 'none' }}>
          <h4>📺 YouTube 트렌드</h4>
          <pre>{JSON.stringify(youtubeTrends, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}

export default AnalysisPanel
