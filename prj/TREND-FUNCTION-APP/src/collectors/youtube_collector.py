from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

import requests


class YouTubeCollector:
    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self, api_key: str | None, timeout_sec: int = 10):
        self.api_key = api_key
        self.timeout_sec = timeout_sec

    def collect_related(self, query: str, max_results: int = 10, region_code: str = "KR") -> List[dict]:
        if not self.api_key:
            return []

        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": min(max_results, 50),
            "regionCode": region_code,
            "order": "relevance",
            "key": self.api_key,
        }

        try:
            response = requests.get(
                f"{self.BASE_URL}/search",
                params=params,
                timeout=self.timeout_sec,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException:
            return []

        items = []
        video_ids: List[str] = []
        for item in data.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            snippet = item.get("snippet", {})
            if not video_id:
                continue
            video_ids.append(video_id)
            items.append(
                {
                    "source": "youtube",
                    "content_id": video_id,
                    "title": snippet.get("title", ""),
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "published_at": snippet.get("publishedAt", datetime.now(timezone.utc).isoformat()),
                    "channel": snippet.get("channelTitle", ""),
                    "excerpt": snippet.get("description", ""),
                    "stats": {
                        "views": 0,
                        "likes": 0,
                        "comments": 0,
                    },
                }
            )

        stats_map = self._get_video_statistics(video_ids)
        for item in items:
            content_id = item.get("content_id")
            if content_id in stats_map:
                item["stats"] = stats_map[content_id]

        return items

    def collect_trending(self, max_results: int = 20, region_code: str = "KR") -> List[dict]:
        if not self.api_key:
            return []

        params = {
            "part": "snippet",
            "chart": "mostPopular",
            "maxResults": min(max_results, 50),
            "regionCode": region_code,
            "key": self.api_key,
        }

        try:
            response = requests.get(
                f"{self.BASE_URL}/videos",
                params=params,
                timeout=self.timeout_sec,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException:
            return []

        items = []
        for item in data.get("items", []):
            video_id = item.get("id")
            snippet = item.get("snippet", {})
            if not video_id:
                continue
            items.append(
                {
                    "source": "youtube",
                    "content_id": video_id,
                    "title": snippet.get("title", ""),
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "published_at": snippet.get("publishedAt", datetime.now(timezone.utc).isoformat()),
                    "channel": snippet.get("channelTitle", ""),
                    "excerpt": snippet.get("description", ""),
                    "stats": {
                        "views": 0,
                        "likes": 0,
                        "comments": 0,
                    },
                }
            )

        stats_map = self._get_video_statistics([item["content_id"] for item in items])
        for item in items:
            content_id = item.get("content_id")
            if content_id in stats_map:
                item["stats"] = stats_map[content_id]

        return items

    def _get_video_statistics(self, video_ids: List[str]) -> Dict[str, dict]:
        if not video_ids or not self.api_key:
            return {}

        params = {
            "part": "statistics",
            "id": ",".join(video_ids[:50]),
            "key": self.api_key,
        }

        try:
            response = requests.get(
                f"{self.BASE_URL}/videos",
                params=params,
                timeout=self.timeout_sec,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException:
            return {}

        stats_map: Dict[str, dict] = {}
        for item in data.get("items", []):
            video_id = item.get("id")
            stats = item.get("statistics", {})
            if not video_id:
                continue
            stats_map[video_id] = {
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
            }
        return stats_map
