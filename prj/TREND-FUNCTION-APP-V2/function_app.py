import json

import azure.functions as func

from src.services.trend_engine import TrendEngine


# Frontend preview calls this API directly without exposing function keys.
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
engine = TrendEngine()


def _read_json(req: func.HttpRequest) -> dict:
    try:
        data = req.get_json()
    except ValueError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    return data


def _json_response(payload: dict, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(payload, ensure_ascii=False),
        status_code=status_code,
        mimetype="application/json",
    )


@app.route(route="trends/meme", methods=["POST"])
def trends_meme(req: func.HttpRequest) -> func.HttpResponse:
    payload = _read_json(req)
    report = engine.generate_meme_report(payload)
    return _json_response(report)


@app.route(route="trends/competitor-keyword", methods=["POST"])
def trends_competitor(req: func.HttpRequest) -> func.HttpResponse:
    payload = _read_json(req)
    report = engine.generate_competitor_report(payload)
    return _json_response(report)


@app.route(route="trends/full-report", methods=["POST"])
def trends_full_report(req: func.HttpRequest) -> func.HttpResponse:
    payload = _read_json(req)
    report = engine.generate_full_report(payload)
    return _json_response(report)


@app.route(route="trends/risk-rising-summary", methods=["POST"])
def trends_risk_rising_summary(req: func.HttpRequest) -> func.HttpResponse:
    payload = _read_json(req)
    report = engine.generate_risk_rising_summary(payload)
    return _json_response(report)


@app.route(route="trends/keyword-summary", methods=["POST"])
def trends_keyword_summary(req: func.HttpRequest) -> func.HttpResponse:
    payload = _read_json(req)
    report = engine.generate_keyword_summary(payload)
    return _json_response(report)


@app.route(route="trends/trending-meme-final", methods=["POST"])
def trends_trending_meme_final(req: func.HttpRequest) -> func.HttpResponse:
    payload = _read_json(req)
    report = engine.generate_trending_meme_report(payload)
    return _json_response(report)


@app.route(route="trends/design-prompt", methods=["POST"])
def trends_design_prompt(req: func.HttpRequest) -> func.HttpResponse:
    payload = _read_json(req)
    report = engine.generate_design_prompt(payload)
    return _json_response(report)


@app.route(route="trends/creative-assets", methods=["POST"])
def trends_creative_assets(req: func.HttpRequest) -> func.HttpResponse:
    payload = _read_json(req)
    report = engine.generate_creative_assets(payload)
    return _json_response(report)


# Backward-compatible legacy routes used by older frontend/Logic App definitions.
@app.route(route="etc_event_scraping", methods=["POST"])
def legacy_etc_event_scraping(req: func.HttpRequest) -> func.HttpResponse:
    payload = _read_json(req)
    report = engine.generate_competitor_report(payload)
    return _json_response(report)


@app.route(route="youtube_trend_scraping", methods=["POST"])
def legacy_youtube_trend_scraping(req: func.HttpRequest) -> func.HttpResponse:
    payload = _read_json(req)
    report = engine.generate_meme_report(payload)
    return _json_response(report)


@app.route(route="analyze_result", methods=["POST"])
def legacy_analyze_result(req: func.HttpRequest) -> func.HttpResponse:
    payload = _read_json(req)
    report = engine.generate_keyword_summary(payload)
    return _json_response(report)
