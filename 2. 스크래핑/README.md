# Azure Functions - Daily Scraper (Python v2 Programming Model)

매일 아침 8시(KST)에 실행되는 Azure Functions Timer Trigger 프로젝트입니다.

## 🎯 프로젝트 개요

이 Azure Functions 프로젝트는 두 가지 주요 기능을 수행합니다:

### 1. 타사 이벤트 스크래퍼 (Card Event Scraper)
- **기술**: Playwright 헤드리스 브라우저
- **목적**: 카드사 이벤트 페이지의 텍스트 콘텐츠 수집
- **함수**: `scrape_card_event_pages()`
- 비동기 처리를 통해 여러 URL에서 효율적으로 데이터 수집

### 2. YouTube 트렌드 스크래퍼 (YouTube Trends Scraper)
- **기술**: YouTube Data API v3
- **목적**: 한국(KR) 지역의 'mostPopular' 인기 급상승 동영상 조회
- **함수**: `get_youtube_trends()`
- API 키를 환경변수(`YOUTUBE_API_KEY`)에서 읽어옴

## 📅 실행 일정

```
크론식: 0 0 8 * * *
→ 매일 08:00:00 (KST 기준)
```

## 🔧 설정 및 실행

### 필수 사항
- Python 3.10 이상
- Azure Functions Core Tools v4
- YouTube API Key (Google Cloud Console에서 발급)

### 설치 방법

```bash
# 1. 프로젝트 디렉토리로 이동
cd "C:\Users\user\Desktop\AI 해커톤\Marketing-Ttok-tti\2. 스크래핑"

# 2. 가상환경 생성 (선택사항)
python -m venv .venv

# 3. 필수 패키지 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
python -m playwright install chromium
```

### 환경변수 설정

`local.settings.json` 파일에서 YouTube API 키 설정:

```json
{
  "Values": {
    "YOUTUBE_API_KEY": "your_youtube_api_key_here"
  }
}
```

### 로컬 실행

```bash
func start
```

## 📦 필수 패키지

| 패키지 | 버전 | 용도 |
|--------|------|------|
| azure-functions | - | Azure Functions 런타임 |
| playwright | ≥1.40.0 | 헤드리스 브라우저 자동화 |
| google-api-python-client | ≥2.100.0 | YouTube Data API v3 클라이언트 |

## 📊 출력 형식

함수는 다음의 JSON 구조로 데이터를 반환합니다:

```json
{
  "timestamp": "2024-06-17T08:00:00+00:00",
  "card_events": [
    {
      "source": "https://example.com/events",
      "text": "이벤트 텍스트 콘텐츠...",
      "scraped_at": "2024-06-17T08:00:00+00:00"
    }
  ],
  "youtube_trends": [
    {
      "title": "동영상 제목",
      "channel": "채널명",
      "views": 1000000,
      "likes": 50000,
      "url": "https://www.youtube.com/watch?v=...",
      "published_at": "2024-06-17T08:00:00Z"
    }
  ],
  "summary": {
    "card_events_count": 1,
    "youtube_trends_count": 10
  }
}
```

## 🔑 YouTube API 키 발급

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. YouTube Data API v3 활성화
4. 인증정보 → API 키 생성
5. 환경변수에 설정

## 📝 주요 함수

### `scrape_card_event_pages()`
```python
async def scrape_card_event_pages() -> list:
    """헤드리스 브라우저로 카드사 이벤트 페이지 스크래핑"""
```
- 비동기 처리로 여러 URL 효율적 수집
- 각 URL별로 전체 페이지 텍스트 추출
- 타임아웃 및 에러 핸들링 포함

### `get_youtube_trends()`
```python
def get_youtube_trends() -> list:
    """YouTube Data API로 한국 인기 동영상 조회"""
```
- 최대 10개의 인기 동영상 조회
- 조회수 기준 정렬
- 동영상 통계(조회수, 좋아요 등) 포함

### `DailyScraperTrigger()`
```python
def DailyScraperTrigger(myTimer: func.TimerRequest) -> None:
    """매일 8시에 실행되는 메인 Timer Trigger 함수"""
```
- 두 스크래퍼 실행 조율
- 결과 병합 및 로깅
- 에러 처리

## ⚠️ 주의사항

1. **Playwright 설정**: 헤드리스 브라우저 사용 시 리소스 제한이 있으므로 필요시 스케일 조정 필요
2. **API 할당량**: YouTube API는 일일 할당량이 있으므로 주의 (기본 10,000 단위)
3. **보안**: `local.settings.json`은 버전 관리에서 제외되므로 배포 시 별도 설정 필요
4. **타임아웃**: Azure Functions는 기본 5분 타임아웃이 있으니 필요시 조정

## 🚀 Azure에 배포

```bash
# 함수 앱 만들기 (한 번만)
az functionapp create --resource-group <resource-group> \
  --consumption-plan-name <plan-name> \
  --runtime python --runtime-version 3.11 \
  --functions-version 4 \
  --name <function-app-name>

# 배포
func azure functionapp publish <function-app-name>
```

## 📖 참고 링크

- [Azure Functions Python Programming Model v2](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python)
- [Playwright Documentation](https://playwright.dev/python/)
- [YouTube Data API v3](https://developers.google.com/youtube/v3)
- [Timer Trigger CRON Expression](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-timer)
