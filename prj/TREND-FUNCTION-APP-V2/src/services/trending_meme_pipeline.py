from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from src.collectors.web_meme_collectors import WebMemeCollector


TITLE_TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣]{2,24}")
YEAR_BORN_RE = re.compile(r"나\s*\d{2}년생\s*[^\s,.!?]{1,16}인데~?")
QUOTE_RE = re.compile(r"[\"'“”‘’]([^\"'“”‘’\n]{3,40})[\"'“”‘’]")

MEME_CUES = {
    "밈",
    "챌린지",
    "릴스",
    "숏폼",
    "유행",
    "트렌드",
    "포맷",
    "회전샷",
    "말랑이",
    "엄미새",
    "백룸",
    "야호",
}

NOISE_TERMS = {
    "고구마팜",
    "wepick",
    "careet",
    "브랜드",
    "마케팅",
    "광고",
    "검색",
    "콘텐츠",
    "방법",
    "가이드",
    "정리",
    "요즘",
    "최근",
}


@dataclass
class TrendingMemeRunConfig:
    lookback_days: int = 50
    max_articles_per_source: Optional[int] = 100
    max_total_posts: int = 300
    max_results: int = 25
    persist_output: bool = True


class TrendingMemePipeline:
    def __init__(self, collector: Optional[WebMemeCollector] = None):
        self.collector = collector or WebMemeCollector()
        self._report_dir = Path(__file__).resolve().parents[2] / "data" / "reports"

    def run(self, payload: dict) -> dict:
        cfg = self._build_config(payload)
        source_docs = self.collector.collect(
            max_articles_per_source=cfg.max_articles_per_source,
            lookback_days=cfg.lookback_days,
            include_article_body=True,
        )
        posts = [doc for docs in source_docs.values() for doc in docs]
        posts.sort(
            key=lambda post: self._parse_iso(post.get("published_at")) or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        posts = posts[: cfg.max_total_posts]

        memes = self._extract_trending_memes(posts, max_results=cfg.max_results)
        keyword_summaries = self._build_keyword_summaries(memes)
        raw_scrape = {
            "schema_version": "v1",
            "stage": "raw_scrape_50d",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "window_days": cfg.lookback_days,
            "collection_config": {
                "lookback_days": cfg.lookback_days,
                "max_articles_per_source": cfg.max_articles_per_source,
                "max_total_posts": cfg.max_total_posts,
                "collect_all_recent": cfg.max_articles_per_source is None,
                "include_article_body": True,
            },
            "doc_counts": {k: len(v) for k, v in source_docs.items()},
            "total_posts": len(posts),
            "posts": posts,
        }
        report = {
            "schema_version": "v1",
            "stage": "trending_meme_pipeline",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "window_days": cfg.lookback_days,
            "collection_config": {
                "lookback_days": cfg.lookback_days,
                "max_articles_per_source": cfg.max_articles_per_source,
                "max_total_posts": cfg.max_total_posts,
                "collect_all_recent": cfg.max_articles_per_source is None,
                "include_article_body": True,
            },
            "source_health": {
                "wepick": "ok" if source_docs.get("wepick") else "empty",
                "gogumafarm": "ok" if source_docs.get("gogumafarm") else "empty",
                "careet": "ok" if source_docs.get("careet") else "empty",
            },
            "base_data": {
                "total_posts": len(posts),
                "doc_counts": {k: len(v) for k, v in source_docs.items()},
                "sample_posts": self._build_sample_posts(posts),
            },
            "trending_memes": memes,
            "keyword_summaries": keyword_summaries,
            "pipeline_steps": [
                {
                    "step": 1,
                    "name": "scrape_50d_with_body",
                    "status": "done",
                    "post_count": len(posts),
                },
                {
                    "step": 2,
                    "name": "save_json_outputs",
                    "status": "pending",
                },
                {
                    "step": 3,
                    "name": "summarize_and_extract_trending_memes",
                    "status": "done",
                    "meme_count": len(memes),
                },
            ],
        }

        if cfg.persist_output:
            saved = self._save_outputs(raw_scrape, report, cfg.lookback_days)
            report["pipeline_steps"][1]["status"] = "done"
            report["saved_files"] = saved
        else:
            report["pipeline_steps"][1]["status"] = "skipped"

        return report

    def _build_keyword_summaries(self, memes: List[dict]) -> List[dict]:
        summaries: List[dict] = []
        for item in memes:
            sample_titles: List[str] = []
            sample_sources: List[str] = []
            for sample in item.get("samples", []):
                title = str(sample.get("title", "")).strip()
                source = str(sample.get("source", "")).strip()
                if title:
                    sample_titles.append(title)
                if source and source not in sample_sources:
                    sample_sources.append(source)
                if len(sample_titles) >= 3:
                    break

            keyword = str(item.get("meme", "")).strip()
            post_count = int(item.get("post_count", 0))
            last_seen_at = str(item.get("last_seen_at", ""))
            summary_text = self._build_summary_text(
                keyword=keyword,
                post_count=post_count,
                sample_sources=sample_sources,
                sample_titles=sample_titles,
                last_seen_at=last_seen_at,
            )

            summaries.append(
                {
                    "keyword": keyword,
                    "post_count": post_count,
                    "summary": summary_text,
                    "source_count": len(sample_sources),
                    "sources": sample_sources,
                    "last_seen_at": last_seen_at,
                    "sample_titles": sample_titles,
                }
            )
        return summaries

    def _build_summary_text(
        self,
        keyword: str,
        post_count: int,
        sample_sources: List[str],
        sample_titles: List[str],
        last_seen_at: str,
    ) -> str:
        if not keyword:
            return ""

        source_part = ""
        if sample_sources:
            source_part = f"{', '.join(sample_sources)} 출처에서"

        title_part = ""
        if sample_titles:
            title_part = f" 대표 사례: {sample_titles[0]}"

        time_part = ""
        if last_seen_at:
            time_part = f" 최근 포착 시점은 {last_seen_at}."

        return (
            f"'{keyword}' 관련 게시물 {post_count}건이 확인됐고 "
            f"{source_part} 반복 언급됩니다."
            f"{title_part}{time_part}"
        ).strip()

    def _build_config(self, payload: dict) -> TrendingMemeRunConfig:
        lookback_days = 50
        max_results = int(payload.get("max_results", 25))
        persist_output = bool(payload.get("persist_output", True))
        max_total_posts = int(payload.get("max_total_posts", 300))

        raw_limit = payload.get("max_articles_per_source", 100)
        try:
            parsed = int(raw_limit)
        except (TypeError, ValueError):
            parsed = 100
        max_per_source = None if parsed <= 0 else parsed

        return TrendingMemeRunConfig(
            lookback_days=lookback_days,
            max_articles_per_source=max_per_source,
            max_total_posts=max(1, max_total_posts),
            max_results=max(1, max_results),
            persist_output=persist_output,
        )

    def _save_outputs(self, raw_scrape: dict, report: dict, lookback_days: int) -> Dict[str, str]:
        self._report_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        raw_latest_path = self._report_dir / f"scraped_posts_{lookback_days}d_latest.json"
        raw_stamped_path = self._report_dir / f"scraped_posts_{lookback_days}d_{ts}.json"
        latest_path = self._report_dir / "trending_memes_latest.json"
        stamped_path = self._report_dir / f"trending_memes_{ts}.json"

        with raw_latest_path.open("w", encoding="utf-8") as fp:
            json.dump(raw_scrape, fp, ensure_ascii=False, indent=2)
        with raw_stamped_path.open("w", encoding="utf-8") as fp:
            json.dump(raw_scrape, fp, ensure_ascii=False, indent=2)

        with latest_path.open("w", encoding="utf-8") as fp:
            json.dump(report, fp, ensure_ascii=False, indent=2)
        with stamped_path.open("w", encoding="utf-8") as fp:
            json.dump(report, fp, ensure_ascii=False, indent=2)

        return {
            "raw_scrape_latest": str(raw_latest_path),
            "raw_scrape_stamped": str(raw_stamped_path),
            "summary_latest": str(latest_path),
            "summary_stamped": str(stamped_path),
        }

    def _build_sample_posts(self, posts: List[dict]) -> List[dict]:
        out = []
        for post in posts[:10]:
            out.append(
                {
                    "source": post.get("source", ""),
                    "title": post.get("title", ""),
                    "url": post.get("url", ""),
                    "published_at": post.get("published_at", ""),
                }
            )
        return out

    def _normalize_phrase(self, text: str) -> str:
        norm = " ".join((text or "").split()).strip().lower()
        norm = norm.strip("'\"“”‘’[]()")
        norm = re.sub(r"\d{2}년생", "○○년생", norm)
        norm = re.sub(r"(○○년생\s+)[^\s,.!?]{1,16}(?=인데)", r"\1○○○", norm)
        return norm

    def _parse_iso(self, value) -> Optional[datetime]:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            return None

    def _extract_candidates(self, title: str, body: str, emphasis: str) -> set[str]:
        text = "\n".join([title or "", body or "", emphasis or ""])
        candidates: set[str] = set()

        for m in YEAR_BORN_RE.finditer(text):
            candidates.add(self._normalize_phrase(m.group(0)))

        for m in QUOTE_RE.finditer(text[:3000]):
            quoted = self._normalize_phrase(m.group(1))
            if any(cue in quoted for cue in MEME_CUES) or "인데~" in quoted:
                candidates.add(quoted)

        tokens = [t.lower() for t in TITLE_TOKEN_RE.findall(title or "")]
        for token in tokens:
            if token in NOISE_TERMS:
                continue
            if token in MEME_CUES:
                candidates.add(token)

        for i in range(len(tokens) - 1):
            phrase = self._normalize_phrase(tokens[i] + " " + tokens[i + 1])
            if any(cue in phrase for cue in MEME_CUES):
                candidates.add(phrase)

        lowered = text.lower()
        for marker in ["엄미새", "말랑이", "백룸", "챌린지", "릴스", "회전샷"]:
            if marker in lowered:
                candidates.add(marker)

        valid: set[str] = set()
        for item in candidates:
            if not item or len(item) < 2:
                continue
            if item in NOISE_TERMS:
                continue
            valid.add(item)
        return valid

    def _extract_trending_memes(self, posts: List[dict], max_results: int) -> List[dict]:
        now = datetime.now(timezone.utc)
        term_tf: Dict[str, float] = {}
        term_df: Dict[str, int] = {}
        term_last_seen: Dict[str, datetime] = {}
        term_samples: Dict[str, List[dict]] = {}

        for post in posts:
            title = str(post.get("title", ""))
            body = str(post.get("body_text", ""))
            emphasis = str(post.get("emphasis_text", ""))
            published = self._parse_iso(post.get("published_at")) or now

            candidates = self._extract_candidates(title, body, emphasis)
            seen_local = set()

            for candidate in candidates:
                boost = 1.0
                if any(cue in candidate for cue in MEME_CUES):
                    boost += 1.5
                if "○○년생" in candidate:
                    boost += 1.2

                term_tf[candidate] = term_tf.get(candidate, 0.0) + boost
                if candidate not in seen_local:
                    term_df[candidate] = term_df.get(candidate, 0) + 1
                    seen_local.add(candidate)

                if candidate not in term_last_seen or published > term_last_seen[candidate]:
                    term_last_seen[candidate] = published

                sample_bucket = term_samples.setdefault(candidate, [])
                if len(sample_bucket) < 4:
                    sample_bucket.append(
                        {
                            "title": title,
                            "url": post.get("url", ""),
                            "source": post.get("source", ""),
                            "published_at": post.get("published_at", ""),
                        }
                    )

        if not term_tf:
            return []

        max_tf = max(term_tf.values())
        max_df = max(term_df.values())

        ranked = []
        for meme, tf in term_tf.items():
            df = term_df.get(meme, 0)
            if df < 2 and not any(cue in meme for cue in MEME_CUES) and "○○년생" not in meme:
                continue

            tf_score = tf / max_tf
            df_score = df / max_df
            last_seen = term_last_seen.get(meme, now)
            hours = max((now - last_seen).total_seconds() / 3600.0, 1.0)
            recency = 1.0 / (1.0 + (hours / (24.0 * 10.0)))

            trend_score = (0.45 * tf_score + 0.35 * df_score + 0.20 * recency) * 100.0

            ranked.append(
                {
                    "meme": meme,
                    "trend_score": round(trend_score, 2),
                    "post_count": int(df),
                    "last_seen_at": last_seen.isoformat(),
                    "samples": term_samples.get(meme, []),
                }
            )

        ranked.sort(key=lambda x: (x.get("trend_score", 0), x.get("post_count", 0)), reverse=True)
        return ranked[:max_results]
