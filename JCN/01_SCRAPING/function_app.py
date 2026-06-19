"""
Azure Functions v2 Python – 카드사 이벤트 데이터 API
─────────────────────────────────────────────────────
엔드포인트:
  GET  /api/events           → 전체 이벤트 JSON
  GET  /api/events?category=여행
  GET  /api/events?company=KB국민카드
  GET  /api/events?q=항공
  GET  /api/events?category=여행&company=KB국민카드&limit=20&offset=0
  GET  /api/categories       → 카테고리별 건수 목록
  POST /api/scrape            → 스크래퍼 실행 후 저장 (Playwright 필요)
"""

import azure.functions as func
import asyncio
import glob
import json
import logging
import os
from datetime import datetime

try:
    from pipeline import run_pipeline  # 스크래핑 파이프라인 래퍼 (Playwright 필요)
except ImportError:
    run_pipeline = None

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


# ─── 공통 헬퍼 ─────────────────────────────────────────────────────────────

def load_latest_events() -> list[dict]:
    """output/ 디렉터리에서 가장 최신 events_detailed_*.json 로드"""
    files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "events_detailed_*.json")))
    if not files:
        raise FileNotFoundError("events_detailed_*.json 파일이 없습니다. /api/scrape 를 먼저 호출하세요.")
    return json.load(open(files[-1], encoding="utf-8"))


def json_response(data, status: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps(data, ensure_ascii=False),
        status_code=status,
        mimetype="application/json",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
        },
    )


def error_response(msg: str, status: int = 400) -> func.HttpResponse:
    return json_response({"error": msg}, status)


# ─── GET /api/events ────────────────────────────────────────────────────────

@app.route(route="events", methods=["GET"])
def get_events(req: func.HttpRequest) -> func.HttpResponse:
    """
    쿼리 파라미터:
      - category : category_new 값으로 필터 (예: 여행, 외식, 교통 …)
      - company  : card_company 값으로 필터 (예: KB국민카드, 롯데카드 …)
      - q        : title / benefit_summary 키워드 검색
      - limit    : 반환 건수 상한 (기본 1000)
      - offset   : 페이지 오프셋 (기본 0)
    """
    try:
        events = load_latest_events()
    except FileNotFoundError as e:
        return error_response(str(e), 404)
    except Exception as e:
        logging.exception("events load error")
        return error_response(f"데이터 로드 실패: {e}", 500)

    category = req.params.get("category", "").strip()
    company  = req.params.get("company",  "").strip()
    q        = req.params.get("q",        "").strip().lower()
    try:
        limit  = int(req.params.get("limit",  "1000"))
        offset = int(req.params.get("offset", "0"))
    except ValueError:
        return error_response("limit / offset 은 정수여야 합니다.")

    # 필터 적용
    if category:
        events = [e for e in events if e.get("category_new") == category]
    if company:
        events = [e for e in events if e.get("card_company") == company]
    if q:
        events = [
            e for e in events
            if q in e.get("title", "").lower()
            or q in e.get("benefit_summary", "").lower()
        ]

    total   = len(events)
    paged   = events[offset : offset + limit]

    return json_response({
        "total":   total,
        "offset":  offset,
        "limit":   limit,
        "count":   len(paged),
        "events":  paged,
    })


# ─── GET /api/categories ────────────────────────────────────────────────────

@app.route(route="categories", methods=["GET"])
def get_categories(req: func.HttpRequest) -> func.HttpResponse:
    """카테고리별 이벤트 건수 및 카드사별 건수 반환"""
    try:
        events = load_latest_events()
    except FileNotFoundError as e:
        return error_response(str(e), 404)
    except Exception as e:
        logging.exception("categories load error")
        return error_response(f"데이터 로드 실패: {e}", 500)

    # 카테고리별 집계
    cat_counts: dict[str, int] = {}
    company_counts: dict[str, int] = {}
    for e in events:
        cat = e.get("category_new", "기타")
        company = e.get("card_company", "")
        cat_counts[cat]         = cat_counts.get(cat, 0) + 1
        company_counts[company] = company_counts.get(company, 0) + 1

    # 건수 내림차순 정렬
    categories = sorted(
        [{"category": k, "count": v} for k, v in cat_counts.items()],
        key=lambda x: x["count"], reverse=True,
    )
    companies = sorted(
        [{"company": k, "count": v} for k, v in company_counts.items()],
        key=lambda x: x["count"], reverse=True,
    )

    return json_response({
        "total": len(events),
        "by_category": categories,
        "by_company": companies,
    })


# ─── POST /api/scrape ───────────────────────────────────────────────────────

@app.route(route="scrape", methods=["POST"])
def post_scrape(req: func.HttpRequest) -> func.HttpResponse:
    """
    전체 스크래핑 파이프라인 실행 (Playwright 필요 – Premium/Dedicated 플랜).
    결과를 output/ 에 저장하고 요약 반환.
    ※ Consumption 플랜에서는 타임아웃(10분) 초과 가능.
    """
    logging.info("POST /api/scrape – 파이프라인 시작")
    try:
        result = asyncio.run(run_pipeline())
        return json_response({
            "status":    "ok",
            "scraped_at": datetime.utcnow().isoformat() + "Z",
            "total":     result["total"],
            "file":      result["file"],
            "by_category": result["by_category"],
        })
    except Exception as e:
        logging.exception("scrape pipeline error")
        return error_response(f"스크래핑 실패: {e}", 500)


# ─── POST /api/etc_event_scraping  ← Logic App이 호출하는 메인 엔드포인트 ──
# Logic App 워크플로 'marketing-ttok-tti-functionappv2-30m' 의
# 'Invoke_etc_event_scraping' 액션이 이 엔드포인트를 POST 호출하고
# 응답 body 를 'Compose_scraping_results' 의 card_events 필드로 넘깁니다.

@app.route(route="etc_event_scraping", methods=["POST"])
def post_etc_event_scraping(req: func.HttpRequest) -> func.HttpResponse:
    """
    Logic App → Compose_scraping_results 용 카드사 이벤트 데이터 반환.
    pre-scraped JSON(output/events_detailed_*.json)을 읽어 즉시 반환합니다.
    응답 구조:
      {
        "scraped_at": "...",
        "total": 249,
        "by_category": [{"category": "여행", "count": 93}, ...],
        "events": [ { card_company, title, benefit_summary, category_new, url, ... } ]
      }
    """
    logging.info("POST /api/etc_event_scraping – 요청 수신")

    try:
        events = load_latest_events()
    except FileNotFoundError as e:
        logging.warning(str(e))
        return error_response(str(e), 404)
    except Exception as e:
        logging.exception("etc_event_scraping load error")
        return error_response(f"데이터 로드 실패: {e}", 500)

    # 요청 body 로 필터 파라미터를 받을 수도 있음 (선택적)
    try:
        body = req.get_json(silent=True) or {}
    except Exception:
        body = {}

    category = body.get("category", "")
    company  = body.get("company",  "")
    q        = body.get("q",        "").lower()

    if category:
        events = [e for e in events if e.get("category_new") == category]
    if company:
        events = [e for e in events if e.get("card_company") == company]
    if q:
        events = [
            e for e in events
            if q in e.get("title", "").lower()
            or q in e.get("benefit_summary", "").lower()
        ]

    # 카테고리별 집계
    cat_counts: dict[str, int] = {}
    for e in events:
        cat = e.get("category_new", "기타")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    by_category = sorted(
        [{"category": k, "count": v} for k, v in cat_counts.items()],
        key=lambda x: x["count"], reverse=True,
    )

    return json_response({
        "scraped_at":  datetime.utcnow().isoformat() + "Z",
        "total":       len(events),
        "by_category": by_category,
        "events":      events,
    })
