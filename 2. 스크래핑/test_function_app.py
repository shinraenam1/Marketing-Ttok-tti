import json
import unittest

import azure.functions as func

from function_app import etc_event_scraping, youtube_trend_scraping


class FunctionAppHttpTests(unittest.TestCase):
    def test_etc_event_scraping_returns_ok(self):
        req = func.HttpRequest(
            method="POST",
            url="http://localhost/api/etc_event_scraping",
            body=json.dumps({"source": "logicapp", "runId": "r1"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        response = etc_event_scraping(req)

        self.assertEqual(response.status_code, 200)
        body = json.loads(response.get_body().decode("utf-8"))
        self.assertEqual(body["function"], "etc_event_scraping")
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["message"], "etc_event_scraping 출력 완료")
        self.assertEqual(body["received"]["source"], "logicapp")

    def test_youtube_trend_scraping_returns_ok(self):
        req = func.HttpRequest(
            method="POST",
            url="http://localhost/api/youtube_trend_scraping",
            body=json.dumps({"source": "logicapp", "runId": "r2"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        response = youtube_trend_scraping(req)

        self.assertEqual(response.status_code, 200)
        body = json.loads(response.get_body().decode("utf-8"))
        self.assertEqual(body["function"], "youtube_trend_scraping")
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["message"], "youtube_trend_scraping 출력 완료")
        self.assertEqual(body["received"]["source"], "logicapp")

    def test_invalid_json_returns_400(self):
        req = func.HttpRequest(
            method="POST",
            url="http://localhost/api/etc_event_scraping",
            body=b"not-json",
            headers={"Content-Type": "application/json"},
        )

        response = etc_event_scraping(req)

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
