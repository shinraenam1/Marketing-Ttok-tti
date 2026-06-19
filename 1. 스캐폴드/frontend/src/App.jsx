import { useState, useEffect } from 'react'
import axios from 'axios'
import AnalysisPanel from './components/AnalysisPanel'
import UserInputForm from './components/UserInputForm'
import PromotionalContent from './components/PromotionalContent'
import './App.css'

function App() {
  const [reportId, setReportId] = useState(null)
  const [analysisSummary, setAnalysisSummary] = useState('')
  const [cardEvents, setCardEvents] = useState(null)
  const [youtubeTrends, setYoutubeTrends] = useState(null)
  const [promotional, setPromotional] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [userParams, setUserParams] = useState(null)

  const FUNCTION_BASE_URL = import.meta.env.VITE_FUNCTION_BASE_URL || '/api'
  const FUNCTION_KEY = import.meta.env.VITE_FUNCTION_KEY || ''

  const buildFunctionUrl = (route) => {
    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    if (!isLocal) {
      return `${FUNCTION_BASE_URL}/${route}`
    }

    const base = FUNCTION_BASE_URL.replace(/\/$/, '')
    if (!FUNCTION_KEY) {
      return `${base}/${route}`
    }

    return `${base}/${route}?code=${FUNCTION_KEY}`
  }

  const toOneLineSummary = (value) => {
    if (!value || typeof value !== 'string') {
      return ''
    }

    const lines = value
      .split('\n')
      .map((line) => line.replace(/^[-#*\s]+/, '').trim())
      .filter(Boolean)

    return lines[0] || ''
  }

  const buildFallbackSummary = (etcData, ytData) => {
    const topCategory = Array.isArray(etcData?.by_category) && etcData.by_category.length > 0
      ? `${etcData.by_category[0].category} 카테고리`
      : '주요 카테고리'

    const topMeme = Array.isArray(ytData?.trends) && ytData.trends.length > 0
      ? ytData.trends[0].keyword
      : ytData?.meme || '밈 키워드'

    return `${topCategory} 이벤트 집중 구간에 '${topMeme}' 밈 키워드를 결합한 프로모션 메시지를 우선 집행하는 전략을 추천합니다.`
  }

  const extractSummaryFromAnalyzeResponse = (analysisResult, etcData, ytData) => {
    if (typeof analysisResult === 'string') {
      return toOneLineSummary(analysisResult) || buildFallbackSummary(etcData, ytData)
    }

    if (analysisResult && typeof analysisResult === 'object') {
      const candidates = [
        analysisResult.summary,
        analysisResult.one_line_summary,
        analysisResult.oneLineSummary,
        analysisResult.insight,
        analysisResult.analysis
      ]

      for (const candidate of candidates) {
        const oneLine = toOneLineSummary(candidate)
        if (oneLine) {
          return oneLine
        }
      }
    }

    return buildFallbackSummary(etcData, ytData)
  }

  // 스크래핑 결과 로드 및 분석
  useEffect(() => {
    const loadLiveData = async () => {
      try {
        setLoading(true)
        const [etcResponse, youtubeResponse] = await Promise.all([
          axios.post(buildFunctionUrl('etc_event_scraping'), {}),
          axios.post(buildFunctionUrl('youtube_trend_scraping'), {})
        ])

        const etcData = etcResponse.data || {}
        const ytData = youtubeResponse.data || {}

        setReportId(`live-${Date.now()}`)
        setCardEvents(etcData)
        setYoutubeTrends(ytData)

        // analyze_result 호출 - OpenAI 분석
        try {
          const analysisResponse = await axios.post(buildFunctionUrl('analyze_result'), {
            card_events: etcData,
            youtube_trends: ytData
          })

          const analysisResult = analysisResponse.data || {}
          setAnalysisSummary(extractSummaryFromAnalyzeResponse(analysisResult, etcData, ytData))
        } catch (analyzeErr) {
          console.error('분석 호출 실패:', analyzeErr)
          setAnalysisSummary(buildFallbackSummary(etcData, ytData))
        }
      } catch (err) {
        setError('스크래핑 데이터 로드 실패')
        console.error('스크래핑 데이터 로드 실패:', err)
      } finally {
        setLoading(false)
      }
    }
    loadLiveData()
  }, [])

  const handleGeneratePromotional = async (params) => {
    setLoading(true)
    setError(null)
    try {
      setUserParams(params)
      
      // Mock promotional content for demo
      const mockContent = `### 1. 배너 광고 (Banner Ad)

**?�드?�인:** 20-30?� 직장?�을 ?�한 ?�션 ?�수 ?�이??추천!
**?�명:** ?�용카드 ?�인??3�??�립?�로 ?�똑?�게 ?�핑?�세??
**?�심 ?�인??**
- 최�? 10만원 캐시�??�택
- 매주 금요???��? ?�벤??
- VIP 고객 ?�선 ?�약 ?�매

### 2. SNS 게시�?(Instagram/Facebook Post)

???�늘???�심???�한 ?�신, ?�신?�게 ?�물???�간!
20-30?� 직장?�이 ?�랑?�는 ?�션 ?�이?�으�?기분 ??UP) ?�켜보세???���?

?�� ?�용카드�?결제?�면 ?�인??3�??�립!
?�� 최�? 10만원 캐시백까지 받아가?�요
?�� ???�운로드 ??추�? 5% ?�인 쿠폰 ?�득

#직장?�패??#?�상??#?�용카드?�택 #?�인?�적�?#?�션추천 #?�핑 #?��???#?�상

### 3. ?�메???�플�?(Email Subject & Body)

**?�목:** [지�??�릭?�세?? ?�션 ?�이??3�??�인??+ 10만원 캐시�? ??

**본문:**
?�녕?�세?? 
바쁜 직장 ?�활 중에??멋진 ?�션?�로 기분???�고 ?�으?��??? ?��

?�?��? 준비했?�니??
?�� ?�용카드 ?�인??3�??�립 ?�벤??
?�� 최�? 10만원 캐시�?
?�� 무료 배송 + 빠른 배송

??기회�??�치지 마세?? 지�?바로 ?�인?�고 최신 ?�션 ?�렌?�로 ?�그?�이?�하?�요!

**CTA:** "지�?바로 ?�핑?�기" ??www.example.com/fashion-event`

      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000))

      const promotional_id = Math.random().toString(36).substring(7)
      const timestamp = new Date().toISOString()

      setPromotional({
        id: promotional_id,
        content: mockContent,
        timestamp: timestamp
      })
    } catch (err) {
      setError(err.message || '?�보�??�성 ?�패')
      console.error('?�보�??�성 ?�러:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>마케팅 분석 대시보드</h1>
        <p>스크래핑 데이터 분석 및 맞춤형 홍보물 생성</p>
      </header>

      <main className="app-main">
        <div className="dashboard-grid">
          <section className="left-panel">
            <div className="panel-header">
              <h2>Step 1-2: 분석 결과</h2>
              {reportId && <span className="report-id">리포트 ID: {reportId.substring(0, 8)}...</span>}
            </div>
            
            {error && <div className="error-banner">{error}</div>}
            
            {(cardEvents || youtubeTrends) && (
              <AnalysisPanel 
                analysisSummary={analysisSummary}
                cardEvents={cardEvents}
                youtubeTrends={youtubeTrends}
              />
            )}
          </section>

          <section className="right-panel">
            <div className="panel-header">
              <h2>Step 3-4: 맞춤형 콘텐츠</h2>
            </div>

            {!promotional ? (
              <UserInputForm 
                onSubmit={handleGeneratePromotional}
                loading={loading}
              />
            ) : (
              <PromotionalContent 
                content={promotional.content}
                params={userParams}
                onReset={() => {
                  setPromotional(null)
                  setUserParams(null)
                }}
              />
            )}
          </section>
        </div>
      </main>

      <footer className="app-footer">
        <p>© 2026 Marketing Ttok-tti | Azure Functions + OpenAI</p>
      </footer>
    </div>
  )
}

export default App
