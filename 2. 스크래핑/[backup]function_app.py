import azure.functions as func
import datetime
import json
import logging
import os
import asyncio

try:
    from playwright.async_api import async_playwright
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    logging.error(f"❌ Import 실패 범인 찾음: {str(e)}")
    raise

app = func.FunctionApp()

# 타사 이벤트 스크래퍼 함수
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
                        "scraped_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
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


@app.timer_trigger(schedule="0 0 8 * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def DailyScraperTrigger(myTimer: func.TimerRequest) -> None:
    """
    매일 아침 8시(KST)에 실행되는 Timer Trigger 함수
    - 타사 이벤트 페이지 스크래핑
    - YouTube 인기 동영상 조회
    두 가지 데이터를 수집하여 JSON으로 반환합니다.
    """
    
    if myTimer.past_due:
        logging.info('The timer is past due!')
    
    logging.info('Daily scraper function started.')
    
    try:
        # 비동기 스크래퍼 실행
        card_events = asyncio.run(scrape_card_event_pages())
        
        # YouTube 트렌드 조회
        youtube_trends = get_youtube_trends()
        
        # 결과 결합
        result = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "card_events": card_events,
            "youtube_trends": youtube_trends,
            "summary": {
                "card_events_count": len(card_events),
                "youtube_trends_count": len(youtube_trends)
            }
        }
        
        logging.info(f"Scraping completed: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
    except Exception as e:
        logging.error(f"Error in DailyScraperTrigger: {str(e)}")
        error_result = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "error": str(e)
        }
        logging.error(json.dumps(error_result, ensure_ascii=False))