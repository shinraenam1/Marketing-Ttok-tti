# TREND-FUNCTION-APP-V2

This is an isolated Azure Functions app intended for new trigger-based workflows.
It is managed separately from the existing root app.

## Endpoint

- POST `/api/trends/trending-meme-final`
- POST `/api/trends/design-prompt`

## What It Does

1. Scrapes posts from the recent 50-day window with article body included.
2. Sorts by latest published date and limits to the newest records.
3. Saves raw and summary JSON outputs.
4. Returns summarized trending meme results.

## Local Run

```powershell
cd apps/trend-function-app-v2
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
func start
```

## Trigger Request Example

```json
{
  "max_results": 20,
  "max_total_posts": 300,
  "max_articles_per_source": 100,
  "persist_output": true
}
```

## Design Prompt Request Example

입력값을 LLM 모델에 보내 이미지 생성 프롬프트를 자동 생성합니다. LLM 실패 시 규칙 기반 생성으로 자동 폴백됩니다.

```json
{
  "primary_keywords": {
    "targets": ["신용카드", "체크카드"],
    "benefits": ["캐시백", "현장할인"],
    "conditions": ["건당 10만원 이상", "월 1회 응모"]
  },
  "free_input": "여름 시즌, 나침반과 카드 이미지 필수",
  "realtime_keyword_summary": "고물가 시대 생활밀착 할인",
  "trend_memes": ["거제 야호"],
  "prompt_only": true
}
```

**응답:**
```json
{
  "schema_version": "v1",
  "generated_at": "2024-01-15T10:30:00.000Z",
  "prompt": "LLM이 생성한 이미지 프롬프트 문장...",
  "inputs": { ... },
  "llm": {
    "enabled": true,
    "used": true,
    "model": "gpt-4"
  }
}
```

**옵션:**
- `free_input`: 추가 의도나 선호사항
- `realtime_keyword_summary`: 실시간 트렌드 요약
- `trend_memes`: 포함할 밈 키워드 배열
- `review_feedback`: 수정 요청 (이 필드를 채우면 LLM이 피드백 반영하여 재생성)
- `previous_prompt`: 이전 생성 프롬프트 (수정 모드에서 기준점으로 사용)
- `prompt_only`: true일 때 간결한 응답 반환

## LLM Configuration

LLM 모델을 통해 입력값 분석 및 프롬프트 생성이 이루어집니다. 설정하지 않으면 규칙 기반 생성으로 폴백됩니다.

**OpenAI와 Azure OpenAI 모두 지원합니다. 엔드포인트 URL에 따라 인증 방식이 자동 감지됩니다.**

### OpenAI 설정:
```
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY={your-openai-key}
OPENAI_MODEL=gpt-4o
```

### Azure OpenAI 설정:
```
OPENAI_BASE_URL=https://{resource-name}.openai.azure.com/v1
OPENAI_API_KEY={your-azure-key}
OPENAI_MODEL={deployment-name}
```

### local.settings.json 예시 (Azure OpenAI):
```json
{
  "Values": {
    "OPENAI_BASE_URL": "https://my-resource.openai.azure.com/v1",
    "OPENAI_API_KEY": "your-azure-api-key",
    "OPENAI_MODEL": "gpt-4"
  }
}
```

### 옵션:
- `OPENAI_API_KEY`: LLM API 키 (필수)
- `OPENAI_MODEL`: 모델 이름 (기본값: gpt-4o)
- `OPENAI_BASE_URL`: 엔드포인트 URL (기본값: https://api.openai.com/v1)
- `LLM_TIMEOUT_SECONDS`: 요청 타임아웃 (기본값: 25초, 범위: 5-60초)

## Output Files

- `data/reports/scraped_posts_50d_latest.json`
- `data/reports/scraped_posts_50d_YYYYMMDD_HHMMSS.json`
- `data/reports/trending_memes_latest.json`
- `data/reports/trending_memes_YYYYMMDD_HHMMSS.json`
