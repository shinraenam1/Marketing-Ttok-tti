import json

import azure.functions as func

from src.services.trend_engine import TrendEngine


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
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
