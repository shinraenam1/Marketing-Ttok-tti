import React, { useState, useEffect } from 'react'
import axios from 'axios'
import AnalysisPanel from './components/AnalysisPanel'
import UserInputForm from './components/UserInputForm'
import PromotionalContent from './components/PromotionalContent'
import './App.css'

function App() {
  const CARD_CATEGORY_STOPWORDS = new Set([
    '카드', '혜택', '이벤트', '프로모션', '할인', '적립', '결제', '최대', '요약', '정리',
    'this', 'month', 'where', 'is', 'the', 'biggest', 'real', 'discount', 'benefit', 'summary',
    'in', 'one', 'view', 'for', 'and', 'with', 'from', 'to', 'of', 'a', 'an', 'vs'
  ])

  const [reportId, setReportId] = useState(null)
  const [analysisSummary, setAnalysisSummary] = useState('')
  const [memeExplanation, setMemeExplanation] = useState('')
  const [cardExplanation, setCardExplanation] = useState('')
  const [memeKeywordExplanations, setMemeKeywordExplanations] = useState({})
  const [cardKeywordExplanations, setCardKeywordExplanations] = useState({})
  const [selectedMemeKeyword, setSelectedMemeKeyword] = useState(null)
  const [selectedCardKeyword, setSelectedCardKeyword] = useState(null)
  const [cardEvents, setCardEvents] = useState(null)
  const [youtubeTrends, setYoutubeTrends] = useState(null)
  const [promotional, setPromotional] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [loadingMessage, setLoadingMessage] = useState('스크래핑 데이터 로드 중...')
  const [userParams, setUserParams] = useState(null)

  const SCRAPER_POLL_INTERVAL_MS = 10000
  const SCRAPER_MAX_WAIT_MS = 15 * 60 * 1000

  const FUNCTION_BASE_URL = import.meta.env.VITE_FUNCTION_BASE_URL
    || 'https://marketing-ttok-tti-functionappv2-bxayc6f7b4f5fhg0.swedencentral-01.azurewebsites.net/api'
  const FUNCTION_KEY = import.meta.env.VITE_FUNCTION_KEY || ''

  const buildFunctionUrl = (route) => {
    const base = FUNCTION_BASE_URL.replace(/\/$/, '')
    const url = `${base}/${route}`
    if (!FUNCTION_KEY) return url
    const hasQuery = url.includes('?')
    return `${url}${hasQuery ? '&' : '?'}code=${encodeURIComponent(FUNCTION_KEY)}`
  }

  const callFunction = async (route, payload = {}) => {
    const url = buildFunctionUrl(route)
    try {
      return await axios.post(url, payload)
    } catch (err) {
      if (err?.response?.status === 405) {
        return axios.get(url)
      }
      throw err
    }
  }

  const callFunctionWithRouteFallback = async (routes, payload = {}) => {
    let lastError = null
    for (const route of routes) {
      try {
        return await callFunction(route, payload)
      } catch (err) {
        lastError = err
        if (err?.response?.status !== 404) {
          throw err
        }
      }
    }
    throw lastError || new Error('함수 엔드포인트 호출에 실패했습니다.')
  }

  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

  const isHtmlLike = (value) => (
    typeof value === 'string' && value.trim().toLowerCase().startsWith('<!doctype html')
  )

  const normalizeCardEvents = (value) => {
    if (!value || isHtmlLike(value)) return null

    const byCategory = Array.isArray(value.by_category) ? value.by_category : []
    if (byCategory.length > 0) return value

    // V2 응답: card_event_insights + related_contents 를 기존 by_category/events 형식으로 변환
    const relatedContents = Array.isArray(value.related_contents) ? value.related_contents : []
    const sourceCounts = {}
    const tokenCounts = {}

    const addToken = (rawToken) => {
      const token = (rawToken || '').trim().toLowerCase()
      if (!token) return
      if (token.length < 2) return
      if (CARD_CATEGORY_STOPWORDS.has(token)) return
      if (/^\d+$/.test(token)) return
      tokenCounts[token] = (tokenCounts[token] || 0) + 1
    }

    const events = relatedContents.map((item, idx) => {
      const source = item?.source || '기타'
      sourceCounts[source] = (sourceCounts[source] || 0) + 1

      const titleTokens = String(item?.title || '').split(/[^\p{L}\p{N}]+/u)
      titleTokens.forEach(addToken)

      const tags = Array.isArray(item?.tags) ? item.tags : []
      tags.forEach(addToken)

      return {
        id: `${source}-${idx}`,
        title: item?.title || '',
        source,
        url: item?.url || '',
      }
    })

    let derivedByCategory = Object.entries(tokenCounts)
      .map(([category, count]) => ({ category, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10)

    if (derivedByCategory.length === 0) {
      derivedByCategory = Object.entries(sourceCounts)
        .map(([category, count]) => ({ category, count }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 10)
    }

    if (derivedByCategory.length === 0 && Array.isArray(value.card_event_insights)) {
      derivedByCategory = value.card_event_insights
        .slice(0, 10)
        .map((insight, idx) => ({
          category: (insight?.top_theme || '').trim() || `카드이벤트 ${idx + 1}`,
          count: (insight?.recommended_angles?.length || 0) + (insight?.copy_seed?.length || 0) || 1,
        }))
    }

    if (derivedByCategory.length === 0) return null

    return {
      by_category: derivedByCategory,
      events,
      schema_version: value.schema_version || 'v1',
    }
  }

  // 응답 형식 정규화:
  //   1. { trends: [{keyword, meme_score}] }  ← 기본 형식
  //   2. { meme_trends: [{keyword, meme_score}] }  ← trends/meme 응답
  //   3. { trending_memes: [{meme, trend_score}] }  ← trends/trending-meme-final 응답
  const normalizeYoutubeTrends = (value) => {
    if (!value || isHtmlLike(value)) return null

    // 형식 2: meme_trends 필드
    if (Array.isArray(value.meme_trends) && value.meme_trends.length > 0) {
      return {
        meme: value.meme_trends[0]?.keyword || '',
        total: value.meme_trends.length,
        trends: value.meme_trends.map(m => ({
          keyword: m.keyword,
          meme_score: m.meme_score || 0,
          growth_rate_pct: m.growth_rate_pct || 0,
        })),
      }
    }

    // 형식 3: trending_memes 필드
    if (Array.isArray(value.trending_memes) && value.trending_memes.length > 0) {
      return {
        meme: value.trending_memes[0]?.meme || '',
        total: value.trending_memes.length,
        trends: value.trending_memes.map(m => ({
          keyword: m.meme || m.keyword || '',
          meme_score: m.trend_score || 0,
          growth_rate_pct: 100,
        })),
      }
    }

    // 형식 1: 기본 trends 필드
    const trends = Array.isArray(value.trends) ? value.trends : []
    if (trends.length === 0) return null
    return value
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

  const buildKeywordExplanationMaps = (etcData, ytData) => {
    const memeMap = {}
    const cardMap = {}

    const memeTop = Array.isArray(ytData?.trends) ? ytData.trends.slice(0, 10) : []
    memeTop.forEach((item) => {
      const keyword = item?.keyword
      if (!keyword) return
      const score = Math.round(Number(item?.meme_score || 0))
      memeMap[keyword] = `최근 확산 점수 ${score}로 반응이 빠르게 올라온 키워드입니다.`
    })

    const cardTop = Array.isArray(etcData?.by_category) ? etcData.by_category.slice(0, 10) : []
    cardTop.forEach((item) => {
      const category = item?.category
      if (!category) return
      const count = Number(item?.count || 0)
      cardMap[category] = `최근 이벤트 언급 ${count}건으로 노출 빈도가 높은 카테고리입니다.`
    })

    return { memeMap, cardMap }
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
        setError(null)

        const startedAt = Date.now()
        let etcData = null
        let ytData = null

        while (Date.now() - startedAt < SCRAPER_MAX_WAIT_MS) {
          const elapsedSec = Math.floor((Date.now() - startedAt) / 1000)
          setLoadingMessage(`스크래퍼 결과 대기 중... (${elapsedSec}s 경과)`)

          const [etcResponse, youtubeResponse] = await Promise.allSettled([
            callFunctionWithRouteFallback(['etc_event_scraping', 'trends/competitor-keyword']),
            callFunctionWithRouteFallback([
              'youtube_trend_scraping',
              'trends/meme',
              'trends/trending-meme-final',
            ])
          ])

          if (etcResponse.status === 'fulfilled') {
            etcData = normalizeCardEvents(etcResponse.value?.data || {})
          }
          if (youtubeResponse.status === 'fulfilled') {
            ytData = normalizeYoutubeTrends(youtubeResponse.value?.data || {})
          }

          if (etcData && ytData) {
            break
          }

          await wait(SCRAPER_POLL_INTERVAL_MS)
        }

        if (!etcData || !ytData) {
          throw new Error('스크래퍼 결과가 아직 준비되지 않았습니다. 잠시 후 다시 시도해주세요.')
        }

        setReportId(`live-${Date.now()}`)
        setCardEvents(etcData)
        setYoutubeTrends(ytData)
        setAnalysisSummary(buildFallbackSummary(etcData, ytData))

        const { memeMap, cardMap } = buildKeywordExplanationMaps(etcData, ytData)
        setMemeKeywordExplanations(memeMap)
        setCardKeywordExplanations(cardMap)

        // analyze_result 호출 - OpenAI 분석
        try {
          const analysisResponse = await callFunctionWithRouteFallback(['analyze_result'], {
            card_events: etcData,
            youtube_trends: ytData
          })

          const analysisResult = analysisResponse.data || {}
          setAnalysisSummary(extractSummaryFromAnalyzeResponse(analysisResult, etcData, ytData))

          // 밈/트렌드 키워드별 설명 생성 (비동기)
          const topMemes = ytData.trends?.slice(0, 10) || []
          if (topMemes.length > 0) {
            callFunction('analyze_result', {
              youtube_trends: { trends: topMemes },
              analysis_type: 'meme_keywords_explanation'
            })
              .then(res => {
                const explanations = res.data?.keyword_explanations || {}
                if (Object.keys(explanations).length > 0) {
                  setMemeKeywordExplanations(explanations)
                }
              })
              .catch(e => console.error('밈 키워드 설명 생성 실패:', e))
          }

          // 카드 이벤트 키워드별 설명 생성 (비동기)
          const topCategories = etcData.by_category?.slice(0, 10) || []
          if (topCategories.length > 0) {
            callFunction('analyze_result', {
              card_events: { by_category: topCategories },
              analysis_type: 'card_keywords_explanation'
            })
              .then(res => {
                const explanations = res.data?.keyword_explanations || {}
                if (Object.keys(explanations).length > 0) {
                  setCardKeywordExplanations(explanations)
                }
              })
              .catch(e => console.error('카드 키워드 설명 생성 실패:', e))
          }
        } catch (analyzeErr) {
          console.error('분석 호출 실패:', analyzeErr)
          setAnalysisSummary(buildFallbackSummary(etcData, ytData))
        }
      } catch (err) {
        setError(err?.message || '스크래핑 데이터 로드 실패')
        console.error('스크래핑 데이터 로드 실패:', err)
      } finally {
        setLoading(false)
        setLoadingMessage('스크래핑 데이터 로드 중...')
      }
    }
    loadLiveData()
  }, [])

  const handleGeneratePromotional = async (params) => {
    setLoading(true)
    setError(null)
    try {
      setUserParams(params)

      const payload = {
        primary_keywords: {
          targets: [params.age, params.job].filter(Boolean),
          benefits: [params.category, params.budget].filter(Boolean),
          conditions: [params.focus].filter(Boolean),
        },
        trend_summary: (selectedMemeKeyword?.explanation || selectedMemeKeyword?.keyword)
          ? [selectedMemeKeyword.explanation || selectedMemeKeyword.keyword]
          : [],
        event_summary: selectedCardKeyword?.explanation || selectedCardKeyword?.category || '',
        free_input: params.free_input || '',
      }

      const res = await callFunctionWithRouteFallback(
        ['trends/design-prompt', 'design-prompt'],
        payload
      )
      const result = res.data || {}
      const generatedPrompt = result.prompt || ''

      const assetRes = await callFunctionWithRouteFallback(
        ['trends/creative-assets'],
        {
          prompt: generatedPrompt,
          include_image: true,
          include_video: true,
        }
      )
      const assets = assetRes.data || {}

      console.log('=== [Step 3-4] 이미지 생성 프롬프트 ===')
      console.log(generatedPrompt)
      console.log('=== payload ===')
      console.log(JSON.stringify(payload, null, 2))
      console.log('=== full response ===')
      console.log(JSON.stringify(result, null, 2))

      const promotional_id = Math.random().toString(36).substring(7)
      const timestamp = new Date().toISOString()

      setPromotional({
        id: promotional_id,
        content: generatedPrompt,
        timestamp: timestamp,
        imageDataUrl: assets?.image?.data_url || '',
        videoDataUrl: assets?.video?.data_url || '',
        assetErrors: Array.isArray(assets?.errors) ? assets.errors : [],
      })
    } catch (err) {
      setError(err.message || '프롬프트 생성 실패')
      console.error('프롬프트 생성 오류:', err)
    } finally {
      setLoading(false)
    }
  }

  const _handleGeneratePromotional_UNUSED = async (params) => {
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

            {loading && !cardEvents && !youtubeTrends && (
              <div className="loading-panel">
                <div className="loading-spinner" />
                <p>{loadingMessage}</p>
              </div>
            )}

            {(cardEvents || youtubeTrends) && (
              <AnalysisPanel 
                analysisSummary={analysisSummary}
                cardEvents={cardEvents}
                youtubeTrends={youtubeTrends}
                memeExplanation={memeExplanation}
                cardExplanation={cardExplanation}
                memeKeywordExplanations={memeKeywordExplanations}
                cardKeywordExplanations={cardKeywordExplanations}
                selectedMemeKeyword={selectedMemeKeyword}
                selectedCardKeyword={selectedCardKeyword}
                onMemeSelect={setSelectedMemeKeyword}
                onCardSelect={setSelectedCardKeyword}
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
                selectedMemeKeyword={selectedMemeKeyword}
                selectedCardKeyword={selectedCardKeyword}
              />
            ) : (
              <PromotionalContent 
                content={promotional.content}
                params={userParams}
                imageDataUrl={promotional.imageDataUrl}
                videoDataUrl={promotional.videoDataUrl}
                assetErrors={promotional.assetErrors}
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
