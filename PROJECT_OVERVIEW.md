# Marketing-Ttok-tti 프로젝트 개요

> 최종 갱신: 2026-06-19  
> GitHub: https://github.com/shinraenam1/Marketing-Ttok-tti  
> Azure Resource Group: `Marketing-Ttok-tti`

---

## 1. 프로젝트 목적

카드사 이벤트 데이터와 SNS/YouTube 밈 트렌드를 결합해  
마케터가 바로 활용할 수 있는 **마케팅 분석 대시보드**를 제공한다.

---

## 2. 전체 구조

```
Marketing-Ttok-tti/
├── 1. 스캐폴드/          # 프론트엔드 (React + Vite)
├── JCN/                  # 카드사 스크래핑 파이프라인 (1회성/실험용)
└── prj/                  # Azure Functions 백엔드
    ├── TREND-FUNCTION-APP/     # V1 (레거시)
    └── TREND-FUNCTION-APP-V2/  # V2 (현재 운영)
```

---

## 3. Azure 리소스

| 리소스 | 이름 | 상태 | 위치 |
|--------|------|------|------|
| Function App (현재 배포 대상) | `Marketing-Ttok-tti-FunctionAppV2` | Running | Sweden Central |
| Function App (신규/실험) | `Marketing-Ttok-tti-FunctionAppV3` | Running | Sweden Central |
| Static Web App (프론트엔드) | `marketing-ttok-tti-web` | - | - |

- **Static Web App URL (production)**: `https://icy-hill-076c01c03.7.azurestaticapps.net`
- **Static Web App URL (preview)**: `https://icy-hill-076c01c03-preview.westeurope.7.azurestaticapps.net`
- **FunctionAppV2 Host**: `marketing-ttok-tti-functionappv2-bxayc6f7b4f5fhg0.swedencentral-01.azurewebsites.net`
- **FunctionAppV3 Host**: `marketing-ttok-tti-functionappv3-bnbra7h6fqhpfva2.swedencentral-01.azurewebsites.net`

---

## 4. 프론트엔드: `1. 스캐폴드/frontend/`

### 기술 스택
- React 18 + Vite 6
- axios

### 주요 파일
```
frontend/
├── index.html
├── package.json
├── manual-dist/          # 수동 빌드 결과물 (swa deploy에 사용)
└── src/
    ├── App.jsx           # 메인 컴포넌트 (API 호출 로직 포함)
    ├── App.css
    ├── main.jsx
    └── components/
        ├── UserInputForm.jsx   # 사용자 조건 입력 폼 (연령대/직업/카테고리/예산/목적)
        ├── UserInputForm.css
        ├── AnalysisPanel.jsx   # 분석 결과 표시 (밈 트렌드 + 카드 이벤트)
        ├── AnalysisPanel.css
        ├── PromotionalContent.jsx  # 프로모션 콘텐츠 출력
        └── PromotionalContent.css
```

### 환경 변수 (`.env`)
```
VITE_FUNCTION_BASE_URL=https://<function-host>/api
VITE_FUNCTION_KEY=<azure-function-key>
```

### 배포 명령
```powershell
# Static Web App 배포 (preview 환경)
$token = (az staticwebapp secrets list --name marketing-ttok-tti-web --resource-group Marketing-Ttok-tti --query properties.apiKey -o tsv)
swa deploy ./manual-dist --env preview --deployment-token $token
```

---

## 5. 백엔드: `prj/TREND-FUNCTION-APP-V2/` (현재 운영)

### 기술 스택
- Python 3 + Azure Functions v2 (HTTP trigger)
- requests, BeautifulSoup4, python-dateutil

### API 엔드포인트 (모두 POST)

| Route | 함수명 | 설명 |
|-------|--------|------|
| `POST /api/trends/meme` | `trends_meme` | 밈 트렌드 리포트 생성 |
| `POST /api/trends/competitor-keyword` | `trends_competitor` | 경쟁사 키워드 분석 |
| `POST /api/trends/full-report` | `trends_full_report` | 전체 통합 리포트 |
| `POST /api/trends/risk-rising-summary` | `trends_risk_rising_summary` | 리스크/급상승 요약 |
| `POST /api/trends/keyword-summary` | `trends_keyword_summary` | 키워드 요약 |
| `POST /api/trends/trending-meme-final` | `trends_trending_meme_final` | 최신 밈 트렌드 최종 결과 (메인 엔드포인트) |

### 디렉토리 구조
```
TREND-FUNCTION-APP-V2/
├── function_app.py           # Azure Functions 진입점 (라우팅 정의)
├── host.json
├── local.settings.sample.json
├── requirements.txt
├── scripts/
│   ├── call_competitor.ps1   # 경쟁사 API 호출 테스트
│   ├── call_full_report.ps1  # 전체 리포트 API 호출 테스트
│   └── run_local.ps1         # 로컬 실행 스크립트
└── src/
    ├── __init__.py
    ├── collectors/
    │   ├── web_meme_collectors.py  # 웹 스크래핑 (캐릿, 위픽 등 밈 큐레이션 사이트)
    │   └── youtube_collector.py    # YouTube Data API v3 수집
    ├── models/
    │   └── safety_policy.json      # 안전 정책 설정
    └── services/
        ├── trend_engine.py          # 핵심 엔진 (generate_* 메서드 모음)
        ├── trending_meme_pipeline.py # 50일 윈도우 크롤링 → 밈 후보 추출 파이프라인
        ├── keyword_expander.py      # 키워드 확장
        ├── scoring.py               # 밈 후보 점수 계산
        └── safety.py                # 콘텐츠 안전 평가
```

### 로컬 실행
```powershell
cd prj/TREND-FUNCTION-APP-V2
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
func start
```

### trending-meme-final 요청 예시
```json
{
  "max_results": 20,
  "max_total_posts": 300,
  "max_articles_per_source": 100,
  "persist_output": true
}
```

### 결과물 파일 (로컬 persist_output=true 시)
- `data/reports/scraped_posts_50d_latest.json`
- `data/reports/trending_memes_latest.json`
- `data/reports/trending_memes_YYYYMMDD_HHMMSS.json`

---

## 6. 백엔드 V1: `prj/TREND-FUNCTION-APP/` (레거시)

V2와 구조 동일. 현재는 유지보수 참조용.  
V2와 코드 거의 동일하나 `trending-meme-final` 엔드포인트 없음.

---

## 7. 카드사 스크래핑: `JCN/01_SCRAPING/`

카드사 이벤트 데이터를 수집하는 별도 파이프라인.  
현재는 독립 실행형 스크립트 (Azure Functions와 분리).

### 수집 대상
| 카드사 | 스크래퍼 파일 |
|--------|--------------|
| KB카드 | `scrapers/kb_card.py` |
| 롯데카드 | `scrapers/lotte_card.py` |
| 삼성카드 | `scrapers/samsung_card.py` |
| 페이북(우리카드) | `scrapers/paybooc.py` |

### 주요 스크립트
- `pipeline.py` — 전체 파이프라인 실행
- `main.py` — 진입점
- `merge_kb.py` — KB카드 결과 병합
- `generate_report.py` / `generate_viewer.py` — HTML 리포트 생성

### 출력 디렉토리: `output/`
- `all_card_events_*.json` — 전체 카드사 이벤트 통합
- `events_detailed_*.json` — 상세 이벤트 데이터
- `kb_card_*.json`, `lotte_card_*.json`, `samsung_card_*.json`, `paybooc_*.json` — 카드사별

---

## 8. 작업 흐름 요약

```
[JCN/01_SCRAPING] 카드사 이벤트 크롤링
        ↓
[TREND-FUNCTION-APP-V2] 밈 트렌드 분석 (웹+YouTube)
        ↓
[1. 스캐폴드/frontend] 대시보드 UI에서 통합 표시
        ↓
[Azure Static Web App] 배포 → icy-hill-076c01c03.7.azurestaticapps.net
```

---

## 9. 자주 쓰는 명령

```powershell
# Function App 로그 스트리밍
az webapp log tail --name Marketing-Ttok-tti-FunctionAppV2 --resource-group Marketing-Ttok-tti

# Static Web App 배포 토큰 조회
az staticwebapp secrets list --name marketing-ttok-tti-web --resource-group Marketing-Ttok-tti --query properties.apiKey -o tsv

# Function App 설정 조회
az functionapp config appsettings list --name Marketing-Ttok-tti-FunctionAppV2 --resource-group Marketing-Ttok-tti -o table

# 로컬 API 테스트 (trending-meme-final)
Invoke-RestMethod -Uri "http://localhost:7071/api/trends/trending-meme-final" -Method POST -Body '{"max_results":5}' -ContentType "application/json"
```
