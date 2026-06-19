import azure.functions as func
import logging
import json
import os
import uuid
import asyncio
from datetime import datetime, timezone
from openai import AzureOpenAI
from azure.data.tables import TableClient

try:
    from playwright.async_api import async_playwright
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    logging.warning(f"Optional dependencies not available: {str(e)}")

app = func.FunctionApp()

# ============================================
# testuser27의 실제 스크래핑 함수들 (복구)
# ============================================

async def scrape_card_event_pages():
    """
    헤드리스 브라우저를 사용하여 카드사 이벤트 페이지의 텍스트를 수집합니다.
    
    Returns:
        list: 카드사 이벤트 정보 리스트 (각 아이템은 {'source': str, 'text': str} 형태)
    """
    events = []
    
    # 스크래핑할 카드사 URL 예시
    card_event_urls = [
        "https://www.samsungcard.com/personal/event/ing/UHPPBE1401M0.jsp",
        "https://card.kbcard.com/BON/DVIEW/HBBMCXCRVNEC0001"
    ]
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            for url in card_event_urls:
                try:
                    await page.goto(url, wait_until="networkidle", timeout=10000)
                    text_content = await page.evaluate("() => document.body.innerText")
                    
                    events.append({
                        "source": url,
                        "text": text_content,
                        "scraped_at": datetime.now(timezone.utc).isoformat()
                    })
                    logging.info(f"Successfully scraped {url}")
                except Exception as e:
                    logging.error(f"Error scraping {url}: {str(e)}")
            
            await browser.close()
    except Exception as e:
        logging.error(f"Playwright error: {str(e)}")
    
    return events


def get_youtube_trends():
    """
    YouTube Data API v3를 사용하여 한국(KR)의 'mostPopular' 인기 급상승 동영상을 조회합니다.
    API 키는 YOUTUBE_API_KEY 환경변수에서 읽습니다.
    
    Returns:
        list: 인기 동영상 정보 리스트 (각 아이템은 {'title': str, 'channel': str, 'views': int, 'url': str} 형태)
    """
    trends = []
    api_key = os.environ.get("YOUTUBE_API_KEY")
    
    if not api_key:
        logging.error("YOUTUBE_API_KEY environment variable not set")
        return trends
    
    try:
        # cache_discovery=False로 oauth2client 관련 file_cache 경고를 방지합니다.
        youtube = build("youtube", "v3", developerKey=api_key, cache_discovery=False)
        
        request = youtube.videos().list(
            part="snippet,statistics",
            chart="mostPopular",
            regionCode="KR",
            maxResults=10
        )
        
        response = request.execute()
        
        for item in response.get("items", []):
            video_id = item["id"]
            snippet = item["snippet"]
            statistics = item["statistics"]
            
            trends.append({
                "title": snippet["title"],
                "channel": snippet["channelTitle"],
                "views": int(statistics.get("viewCount", 0)),
                "likes": int(statistics.get("likeCount", 0)),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "published_at": snippet["publishedAt"]
            })
            
        logging.info(f"Successfully retrieved {len(trends)} YouTube trends")
    except HttpError as e:
        logging.error(f"YouTube API error: {e}")
    except Exception as e:
        logging.error(f"Error fetching YouTube trends: {str(e)}")
    
    return trends


_openai_client: AzureOpenAI | None = None

def _get_openai_client() -> AzureOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AzureOpenAI(
            api_key=os.environ["AZURE_OPENAI_KEY"],
            api_version="2024-12-01-preview",
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        )
    return _openai_client


def _get_table_client() -> TableClient:
    return TableClient.from_connection_string(
        conn_str=os.environ["TABLE_STORAGE_CONNECTION_STRING"],
        table_name="marketinganalytics"
    )


def _parse_request_payload(req: func.HttpRequest) -> tuple[dict, str]:
    raw_body = req.get_body().decode("utf-8") if req.get_body() else ""
    if not raw_body.strip():
        return {}, ""

    try:
        return req.get_json(), raw_body
    except ValueError:
        raise ValueError("요청 본문은 JSON 형식이어야 합니다.")


def _log_info(function_name: str, payload: dict, raw_body: str) -> None:
    logging.info(
        "[info] function=%s timestamp=%s payloadKeys=%s rawBodyLength=%d",
        function_name,
        datetime.now(timezone.utc).isoformat(),
        list(payload.keys()),
        len(raw_body),
    )

# 1. Logic App에서 직접 호출하는 함수 (etc_event_scraping)
@app.route(route="etc_event_scraping", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def etc_event_scraping(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("[etc_event_scraping] START - testuser27 스크래핑 기능 호출")

    try:
        payload, raw_body = _parse_request_payload(req)
        _log_info("etc_event_scraping", payload, raw_body)

        # testuser27의 실제 스크래핑 실행 (Playwright 기반)
        try:
            card_events = asyncio.run(scrape_card_event_pages())
            logging.info(f"[etc_event_scraping] 카드사 이벤트 {len(card_events)}개 수집")
        except Exception as e:
            logging.error(f"[etc_event_scraping] Playwright 스크래핑 실패: {str(e)}")
            card_events = []

        response = {
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "total": len(card_events),
            "by_category": [],
            "events": card_events
        }
        
        logging.info("[etc_event_scraping] END status=ok")
        return func.HttpResponse(
            json.dumps(response, ensure_ascii=False),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as e:
        logging.error(f"[etc_event_scraping] ERROR: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            mimetype="application/json",
            status_code=400,
        )


# 2. Logic App에서 직접 호출하는 함수 (youtube_trend_scraping)
@app.route(route="youtube_trend_scraping", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def youtube_trend_scraping(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("[youtube_trend_scraping] START - testuser27 YouTube API 호출")

    try:
        payload, raw_body = _parse_request_payload(req)
        _log_info("youtube_trend_scraping", payload, raw_body)

        # testuser27의 실제 YouTube 트렌드 스크래핑
        youtube_trends = get_youtube_trends()
        logging.info(f"[youtube_trend_scraping] YouTube 트렌드 {len(youtube_trends)}개 수집")

        response = {
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "total": len(youtube_trends),
            "trends": youtube_trends,
            "meme": "거제 야호"
        }
        logging.info("[youtube_trend_scraping] END status=ok")
        return func.HttpResponse(
            json.dumps(response, ensure_ascii=False),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as e:
        logging.error(f"[youtube_trend_scraping] ERROR: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            mimetype="application/json",
            status_code=400,
        )


# 3. 두 스크래퍼 결과를 합쳐서 Azure OpenAI로 분석하는 함수
@app.route(route="analyze_result", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def analyze_result(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("[analyze_result] START")

    try:
        payload, raw_body = _parse_request_payload(req)
        _log_info("analyze_result", payload, raw_body)

        card_events = payload.get("card_events", {})
        youtube_trends = payload.get("youtube_trends", {})

        prompt = _build_analysis_prompt(card_events, youtube_trends)
        logging.info("[analyze_result] OpenAI 분석 요청 시작")

        client = _get_openai_client()
        chat_response = client.chat.completions.create(
            model=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-5.5"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "당신은 마케팅 데이터 분석 전문가입니다. "
                        "카드사 이벤트 정보와 YouTube 트렌드 데이터를 바탕으로 "
                        "마케팅 인사이트를 한국어로 간결하게 정리해주세요."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
                max_completion_tokens=1000,
        )

        analysis_text = chat_response.choices[0].message.content
        logging.info("[analyze_result] OpenAI 분석 완료")

        # Generate unique reportId
        report_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # Prepare report data for Table Storage
        report_entity = {
            "PartitionKey": "marketing-analysis",
            "RowKey": report_id,
            "timestamp": timestamp,
            "analysis": analysis_text,
            "card_events_summary": json.dumps(card_events, ensure_ascii=False)[:32000],  # Table Storage 32KB limit
            "youtube_trends_summary": json.dumps(youtube_trends, ensure_ascii=False)[:32000],
        }

        # Save to Table Storage
        try:
            table_client = _get_table_client()
            table_client.create_table_if_not_exists()
            table_client.upsert_entity(report_entity)
            logging.info(f"[analyze_result] Table Storage에 리포트 저장: {report_id}")
        except Exception as table_error:
            logging.error(f"[analyze_result] Table Storage 저장 실패: {str(table_error)}")
            # 저장 실패해도 분석 결과는 반환

        response = {
            "function": "analyze_result",
            "status": "ok",
            "message": "analyze_result 출력 완료",
            "reportId": report_id,
            "analysis": analysis_text,
            "input_summary": {
                "card_events_received": bool(card_events),
                "youtube_trends_received": bool(youtube_trends),
            },
            "timestamp": timestamp,
        }
        logging.info("[analyze_result] END status=ok")
        return func.HttpResponse(
            json.dumps(response, ensure_ascii=False),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as e:
        logging.error(f"[analyze_result] ERROR: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            mimetype="application/json",
            status_code=500,
        )


def _build_analysis_prompt(card_events: dict, youtube_trends: dict) -> str:
    card_data = json.dumps(card_events, ensure_ascii=False, indent=2)
    youtube_data = json.dumps(youtube_trends, ensure_ascii=False, indent=2)
    return f"""아래 두 가지 데이터를 분석하여 마케팅 인사이트를 제공해주세요.

## 카드사 이벤트 데이터
{card_data}

## YouTube 트렌드 데이터
{youtube_data}

다음 항목을 포함해서 분석해주세요:
1. 카드사 이벤트 주요 혜택 요약 (3줄 이내)
2. YouTube 트렌드 주요 키워드 및 소비자 관심사 (3줄 이내)
3. 두 데이터를 연결한 마케팅 기회 및 제안 (3가지)
"""


# 4. Table Storage에서 리포트 조회
@app.route(route="report_service", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def report_service(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("[report_service] START")

    try:
        payload, raw_body = _parse_request_payload(req)
        _log_info("report_service", payload, raw_body)

        report_id = payload.get("reportId")
        if not report_id:
            return func.HttpResponse(
                json.dumps({"error": "reportId가 필요합니다."}, ensure_ascii=False),
                mimetype="application/json",
                status_code=400,
            )

        table_client = _get_table_client()
        table_client.create_table_if_not_exists()
        
        entity = table_client.get_entity(partition_key="marketing-analysis", row_key=report_id)
        
        response = {
            "function": "report_service",
            "status": "ok",
            "message": "report_service 출력 완료",
            "reportId": report_id,
            "timestamp": entity.get("timestamp"),
            "analysis": entity.get("analysis"),
            "card_events_summary": json.loads(entity.get("card_events_summary", "{}")),
            "youtube_trends_summary": json.loads(entity.get("youtube_trends_summary", "{}")),
        }
        logging.info("[report_service] END status=ok")
        return func.HttpResponse(
            json.dumps(response, ensure_ascii=False),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as e:
        logging.error(f"[report_service] ERROR: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            mimetype="application/json",
            status_code=400,
        )


# 5. 사용자 입력 파라미터를 받아 홍보물 생성
@app.route(route="generate_promotional", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def generate_promotional(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("[generate_promotional] START")

    try:
        payload, raw_body = _parse_request_payload(req)
        _log_info("generate_promotional", payload, raw_body)

        report_id = payload.get("reportId")
        target_age_group = payload.get("target_age_group", "전체")
        target_job = payload.get("target_job", "전체")
        category_preference = payload.get("category_preference", "전체")
        budget_allocation = payload.get("budget_allocation", "일반")
        marketing_focus = payload.get("marketing_focus", "전체")

        if not report_id:
            return func.HttpResponse(
                json.dumps({"error": "reportId가 필요합니다."}, ensure_ascii=False),
                mimetype="application/json",
                status_code=400,
            )

        # Table Storage에서 리포트 조회
        table_client = _get_table_client()
        table_client.create_table_if_not_exists()
        entity = table_client.get_entity(partition_key="marketing-analysis", row_key=report_id)
        original_analysis = entity.get("analysis", "")
        card_events_summary = entity.get("card_events_summary", "{}")
        youtube_trends_summary = entity.get("youtube_trends_summary", "{}")

        # 사용자 입력 기반 프롬프트 생성
        prompt = _build_promotional_prompt(
            original_analysis,
            card_events_summary,
            youtube_trends_summary,
            target_age_group,
            target_job,
            category_preference,
            budget_allocation,
            marketing_focus
        )

        logging.info("[generate_promotional] OpenAI 홍보물 생성 요청 시작")

        client = _get_openai_client()
        chat_response = client.chat.completions.create(
            model=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-5.5"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "당신은 전문 마케팅 카피라이터입니다. "
                        "제시된 분석 결과와 타겟 오디언스 정보를 기반으로 "
                        "채널별 홍보물을 한국어로 작성해주세요."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=2000,
        )

        promotional_content = chat_response.choices[0].message.content
        logging.info("[generate_promotional] OpenAI 홍보물 생성 완료")

        # 생성된 홍보물을 Table Storage에 저장
        promotional_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        promotional_entity = {
            "PartitionKey": "marketing-promotional",
            "RowKey": promotional_id,
            "report_id": report_id,
            "timestamp": timestamp,
            "promotional_content": promotional_content,
            "target_age_group": target_age_group,
            "target_job": target_job,
            "category_preference": category_preference,
            "budget_allocation": budget_allocation,
            "marketing_focus": marketing_focus,
        }

        try:
            table_client.upsert_entity(promotional_entity)
            logging.info(f"[generate_promotional] 홍보물 저장 완료: {promotional_id}")
        except Exception as table_error:
            logging.error(f"[generate_promotional] Table Storage 저장 실패: {str(table_error)}")

        response = {
            "function": "generate_promotional",
            "status": "ok",
            "message": "generate_promotional 출력 완료",
            "promotionalId": promotional_id,
            "reportId": report_id,
            "promotional_content": promotional_content,
            "user_parameters": {
                "target_age_group": target_age_group,
                "target_job": target_job,
                "category_preference": category_preference,
                "budget_allocation": budget_allocation,
                "marketing_focus": marketing_focus,
            },
            "timestamp": timestamp,
        }
        logging.info("[generate_promotional] END status=ok")
        return func.HttpResponse(
            json.dumps(response, ensure_ascii=False),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as e:
        logging.error(f"[generate_promotional] ERROR: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            mimetype="application/json",
            status_code=500,
        )


def _build_promotional_prompt(
    original_analysis: str,
    card_events_summary: str,
    youtube_trends_summary: str,
    target_age_group: str,
    target_job: str,
    category_preference: str,
    budget_allocation: str,
    marketing_focus: str,
) -> str:
    return f"""아래 마케팅 분석 결과와 타겟 오디언스 정보를 바탕으로 매력적인 홍보물을 생성해주세요.

## 기본 마케팅 분석
{original_analysis}

## 타겟 오디언스 정보
- 연령대: {target_age_group}
- 직업/직군: {target_job}
- 관심 카테고리: {category_preference}
- 예산 할당: {budget_allocation}
- 마케팅 포커스: {marketing_focus}

## 요청사항
다음 3가지 형식의 홍보물을 생성해주세요 (각각 구분 명확하게):

### 1. 배너 광고 (Banner Ad)
- 50글자 이내 임팩트 있는 헤드라인 1개
- 설명문 100글자 이내 1개
- 핵심 포인트 3개

### 2. SNS 게시물 (Instagram/Facebook Post)
- 이모지를 포함한 캐치한 오프닝
- 본문 (200글자 이내)
- 해시태그 5-10개

### 3. 이메일 템플릿 (Email Subject & Body)
- 이메일 제목 (60글자 이내)
- 이메일 본문 (300글자 이내)
- CTA(Call-to-Action) 문구

모든 콘텐츠는 위의 타겟 오디언스에 맞는 톤과 메시지로 작성해주세요.
"""
