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

  const CATEGORY_RULES = [
    ['여행', [
      '여행', '해외', '항공', '항공권', '호텔', '숙박', '리조트', '펜션', '투어',
      '크루즈', '면세점', '면세', '에어비앤비', '트립닷컴', '아고다', '호텔스닷컴',
      '라쿠텐트래블', '렌탈카스닷컴', '에어알로', '클룩', '웹투어', '와이페이모어',
      '레고랜드', '에버랜드', '롯데월드', '놀이공원', '테마파크', '일본', '유럽',
      '미국', '중국', '태국', '싱가포르', '하와이', '나리타', '하네다', '오사카',
      '후쿠오카', '파리', '런던', '바르셀로나', '홍콩', '마카오', '코나', '발리',
      '태국여행', '관광', '비스터', '라발레', '라로카', 'ihg', '프리퍼드호텔',
      '펜타포트', '페스티벌', '국내선', '국제선'
    ]],
    ['외식', [
      '외식', '식당', '레스토랑', '카페', '커피', '치킨', '피자', '배달', '버거',
      '스타벅스', '맥도날드', '푸드', '맛집', '메가mgc커피', '교촌허니콤보',
      '다이닝', '스테이크', '스시', '라멘', '수블리엠', '이자카야', '쿠팡이츠', '배달의민족'
    ]],
    ['교통', [
      '주유', '주유소', '주유권', '자동차', '렌탈', '렌트', '택시', '고속도로', '주차',
      '전기차', 'ev충전', '충전', '버스', '지하철', '기차', '철도', '고속버스',
      '해외운전', '국내선항공', '항공운임', 'ev카드', '스피드메이트', '티스테이션', '트랩'
    ]],
    ['문화레저', [
      '문화', '공연', '영화', '도서', '음악', '전시', '스포츠', '레저', '골프', '야구',
      'cgv', '메가박스', '볼링', '당첨확인', '콘서트', '미술관', '박물관', '두산베어스',
      '펜타포트', '인천펜타포트', '락페스티벌', '월드컵', '응원키트', '운동권'
    ]],
    ['헬스뷰티', [
      '헬스', '뷰티', '화장품', '피부', '미용', '헬스장', '피트니스', '요가', '필라테스',
      '올리브영', '다이소', '임산', '병원', '약국', '의료', '마스크팩', '마스크', '스킨케어'
    ]],
    ['디지털통신', [
      '디지털', '통신', '휴대폰', '전자', '휴대폰포로콘', '게임', 'ott', '스트리밍', '인터넷',
      '넷플릭스', '구독', '앱', 'sk', 'kt', 'lg유플', 'skt', 'kt스카이라이프', '단말기',
      't라이트', 'liivmii', 'lg헬로비전', '케이블tv', 'ai플랫폼', 'ai활용', '인터넷전화',
      '휴대폰 단말기', '단말기값', 'esim', '데이터 로밍'
    ]],
    ['금융할부', [
      '무이자', '할부', '보험', '대출', '연회비', '마일리지', '리워드', '포인트적립', '포인트리',
      '포인트 제공', 'h.point', '삼성화재', '현대화재', '자동차보험', '미니코부매스터',
      '파이낸싱', '시세로인튀리튬', '정기결제', '자동납부', '적립마일리지', 'p마일리지',
      '국세', '지방세', '소상공인', '연회비 100%'
    ]],
    ['쇼핑', [
      '백화점', '마트', '온라인쇼핑', '이마트', '롯데마트', '홈플러스', 'g마켓', '쿠팡', '11번가',
      '아울렛', '시세이즈마션', '로드샵시쿠니승마승', '뷔스트마션', '히아 레이드스마선',
      '쇼핑', '클리어마션', 'h.이포인트', '쿠팡와우', '네이버플러스스토어', '슬포츠마존',
      '시세통통말이제도', '무통보너스마스터', '비스터업설그라니스포리툼'
    ]],
    ['생활편의', [
      '편의점', '교육', '학원', '세탁', '구청요금', 'cu', 'gs25', '세븐일레븐', '미니스톱',
      '이마트24', '팸샵', '주거', '화백', '캐릭팩키지', '중국집데일레븐'
    ]],
    ['시즌취미', [
      '시즌', '문화상품권', '도서제당', '스탬프', '월드컵', '운동원', '여름', '겨울',
      '보열스노우파트 코리아', '새해', '추석', '설날', 'summer', 'winter', '황금연휴',
      '명절', '발렌타인'
    ]],
  ]

  const ALLOWED_CATEGORY_NAMES = new Set(CATEGORY_RULES.map(([name]) => name))

  const toCategoryText = (item) => {
    const values = [
      item?.title,
      item?.subtitle,
      item?.benefit_summary,
      item?.summary,
      item?.snippet,
      item?.source,
      item?.description,
      ...(Array.isArray(item?.categories) ? item.categories : []),
      ...(Array.isArray(item?.tags) ? item.tags : []),
      ...(Array.isArray(item?.matched_terms) ? item.matched_terms : []),
    ]
    return values
      .filter(Boolean)
      .map((value) => String(value).toLowerCase())
      .join(' ')
  }

  const categorizeEvent = (text) => {
    for (const [category, keywords] of CATEGORY_RULES) {
      if (keywords.some((kw) => text.includes(kw.toLowerCase()))) {
        return category
      }
    }
    return null
  }

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

      const titleTokens = String(item?.title || '').split(/[^\p{L}\p{N}]+/u)
      titleTokens.forEach(addToken)

      const tags = Array.isArray(item?.tags) ? item.tags : []
      tags.forEach(addToken)

      return {
        id: `${source}-${idx}`,
        title: item?.title || '',
        subtitle: item?.subtitle || '',
        benefit_summary: item?.benefit_summary || item?.summary || item?.snippet || '',
        categories: Array.isArray(item?.categories) ? item.categories : [],
        tags,
        matched_terms: Array.isArray(item?.matched_terms) ? item.matched_terms : [],
        source,
        url: item?.url || '',
      }
    })

    // CATEGORY_RULES 기반 분류만 허용
    const categoryCount = {}
    events.forEach((event) => {
      const categoryText = toCategoryText(event)
      const cat = categorizeEvent(categoryText)
      if (!cat) return
      if (!ALLOWED_CATEGORY_NAMES.has(cat)) return
      categoryCount[cat] = (categoryCount[cat] || 0) + 1
    })

    let derivedByCategory = Object.entries(categoryCount)
      .map(([category, count]) => ({ category, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10)

    // 폴백도 CATEGORY_RULES 내부 키워드에 한해 매핑
    if (derivedByCategory.length === 0) {
      const tokenCategoryCount = {}
      Object.entries(tokenCounts).forEach(([token, count]) => {
        const cat = categorizeEvent(token)
        if (!cat) return
        tokenCategoryCount[cat] = (tokenCategoryCount[cat] || 0) + count
      })
      derivedByCategory = Object.entries(tokenCategoryCount)
        .map(([category, count]) => ({ category, count }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 10)
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
