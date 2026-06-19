from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from src.collectors.web_meme_collectors import WebMemeCollector
from src.collectors.youtube_collector import YouTubeCollector
from src.services.creative_asset_generator import CreativeAssetGenerator
from src.services.design_prompt_builder import DesignPromptBuilder
from src.services.keyword_expander import expand_keyword
from src.services.safety import analyze_text_risk, evaluate_contents_safety, safe_copy_suggestion
from src.services.scoring import extract_meme_candidates, score_related_content, tokenize
from src.services.trending_meme_pipeline import TrendingMemePipeline


GENERIC_TOPIC_BLACKLIST = {
    "브랜드",
    "콘텐츠",
    "트렌드",
    "레퍼런스",
    "크리에이터",
    "북마크",
    "유행중",
    "마케팅",
    "공식",
    "방법",
    "정리",
    "총정리",
    "고구마팜",
    "careet",
    "wepick",
    "캐릿",
    "위픽",
}

TOPIC_FUNCTION_WORDS = {
    "점령한",
    "피드를",
    "피드",
    "하는",
    "하고",
    "하는데",
    "되는",
    "있는",
    "있고",
    "있다",
    "요즘",
    "지금",
    "최근",
    "국내외",
    "글로벌",
    "핫한",
}

TOPIC_CUE_TERMS = {
    "밈",
    "챌린지",
    "샷",
    "회전샷",
    "릴스",
    "포맷",
    "굿즈",
    "경제",
    "소비",
}

GENERIC_AD_BLOCKLIST = {
    "글로벌",
    "국내외",
    "마케팅",
    "레퍼런스",
    "크리에이터",
    "브랜드",
    "콘텐츠",
    "트렌드",
    "포맷",
    "유행",
    "북마크",
    "15인",
    "2026년",
}

PHRASE_NOISE_TOKENS = {
    "빠진",
    "달라야",
    "반복되는",
    "방문객과",
    "요즘",
    "6월",
    "7월",
    "8월",
    "9월",
    "10월",
    "11월",
    "12월",
    "vip의",
}


class TrendEngine:
    def __init__(self):
        self.web_collector = WebMemeCollector()
        self.youtube_collector = YouTubeCollector(api_key=os.getenv("YOUTUBE_API_KEY"))
        self.trending_meme_pipeline = TrendingMemePipeline(collector=self.web_collector)
        self.design_prompt_builder = DesignPromptBuilder()
        self.creative_asset_generator = CreativeAssetGenerator()
        self._snapshot_path = Path(__file__).resolve().parents[2] / "data" / "youtube_keyword_snapshot.json"
        self._site_topic_snapshot_path = Path(__file__).resolve().parents[2] / "data" / "site_topic_snapshot.json"

    def generate_design_prompt(self, payload: dict) -> dict:
        return self.design_prompt_builder.generate(payload)

    def generate_creative_assets(self, payload: dict) -> dict:
        return self.creative_asset_generator.generate(payload)

    def generate_trending_meme_report(self, payload: dict) -> dict:
        return self.trending_meme_pipeline.run(payload)

    def generate_meme_report(self, payload: dict) -> dict:
        lookback_days = int(payload.get("lookback_days", 90))
        max_results = int(payload.get("max_results", 20))
        policy_actions = payload.get("safety_policy")
        per_source_limit = self._resolve_collection_limit(payload, default_limit=20)

        source_docs = self.web_collector.collect(max_articles_per_source=per_source_limit, lookback_days=lookback_days)
        documents = [doc for docs in source_docs.values() for doc in docs]

        memes = extract_meme_candidates(documents, top_k=max_results)
        filtered_memes: List[dict] = []
        blocked_terms: List[str] = []
        risk_flags: List[str] = []

        for meme in memes:
            risk = analyze_text_risk(meme.get("keyword", ""), policy_actions=policy_actions)
            if risk["blocked_terms"]:
                blocked_terms.extend(risk["blocked_terms"])
                risk_flags.extend(risk["risk_flags"])
                continue
            meme_item = dict(meme)
            meme_item["risk_flags"] = risk["risk_flags"]
            filtered_memes.append(meme_item)

        topic_clusters = self._build_topic_clusters(
            documents=documents,
            meme_keywords=filtered_memes,
            max_topics=max_results,
        )

        return {
            "schema_version": "v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "window_days": lookback_days,
            "source_health": {
                "wepick": "ok" if source_docs.get("wepick") else "empty",
                "gogumafarm": "ok" if source_docs.get("gogumafarm") else "empty",
                "careet": "ok" if source_docs.get("careet") else "empty",
                "youtube": "disabled" if not os.getenv("YOUTUBE_API_KEY") else "ok",
            },
            "meme_trends": filtered_memes,
            "topic_clusters": topic_clusters,
            "ad_candidate_keywords": self._build_ad_candidate_keywords(topic_clusters, max_keywords=10),
            "trend_keyword_quality": self._build_trend_keyword_quality(topic_clusters),
            "blocked_terms": sorted(set(blocked_terms)),
            "risk_flags": sorted(set(risk_flags)),
            "safety_policy_applied": policy_actions or {},
            "collection_config": {
                "lookback_days": lookback_days,
                "collect_all_recent": per_source_limit is None,
                "max_articles_per_source": per_source_limit,
            },
        }

    def generate_competitor_report(self, payload: dict) -> dict:
        keyword = str(payload.get("input_keyword", "")).strip()
        lookback_days = int(payload.get("lookback_days", 90))
        max_results = int(payload.get("max_results", 20))
        include_youtube = bool(payload.get("include_youtube", True))
        region_code = str(payload.get("country", "KR")).upper()
        policy_actions = payload.get("safety_policy")
        per_source_limit = self._resolve_collection_limit(payload, default_limit=25)

        expanded = expand_keyword(keyword)
        source_docs = self.web_collector.collect(max_articles_per_source=per_source_limit, lookback_days=lookback_days)
        web_contents = [doc for docs in source_docs.values() for doc in docs]

        yt_contents: List[dict] = []
        if keyword and include_youtube:
            yt_contents = self.youtube_collector.collect_related(
                keyword,
                max_results=10,
                region_code=region_code,
            )

        all_contents = web_contents + yt_contents
        scored_contents = score_related_content(all_contents, expanded)[:max_results]
        safe_contents, safety_summary = evaluate_contents_safety(
            scored_contents,
            policy_actions=policy_actions,
        )
        safe_seed = safe_copy_suggestion(f"{keyword} benefit summary in one view")

        return {
            "schema_version": "v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "window_days": lookback_days,
            "input_keyword": keyword,
            "normalized_keywords": expanded,
            "related_contents": safe_contents,
            "blocked_terms": safety_summary["blocked_terms"],
            "risk_flags": safety_summary["risk_flags"],
            "safe_copy_suggestion": safe_seed,
            "safety_policy_applied": policy_actions or {},
            "card_event_insights": self._build_card_event_insights(keyword, safe_contents),
        }

    def generate_full_report(self, payload: dict) -> dict:
        keyword = str(payload.get("input_keyword", "")).strip()

        meme_part = self.generate_meme_report(payload)
        competitor_part = self.generate_competitor_report(payload)

        return {
            "schema_version": "v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "input_keyword": keyword,
            "normalized_keywords": competitor_part["normalized_keywords"],
            "source_health": meme_part["source_health"],
            "meme_trends": meme_part["meme_trends"],
            "topic_clusters": meme_part.get("topic_clusters", []),
            "ad_candidate_keywords": meme_part.get("ad_candidate_keywords", []),
            "trend_keyword_quality": meme_part.get("trend_keyword_quality", {}),
            "related_contents": competitor_part["related_contents"],
            "blocked_terms": sorted(
                set(meme_part.get("blocked_terms", []))
                .union(set(competitor_part.get("blocked_terms", [])))
            ),
            "risk_flags": sorted(
                set(meme_part.get("risk_flags", []))
                .union(set(competitor_part.get("risk_flags", [])))
            ),
            "safe_copy_suggestion": competitor_part.get("safe_copy_suggestion", ""),
            "safety_policy_applied": competitor_part.get("safety_policy_applied", {}),
            "card_event_insights": competitor_part["card_event_insights"],
        }

    def generate_risk_rising_summary(self, payload: dict) -> dict:
        lookback_days = int(payload.get("lookback_days", 90))
        max_results = int(payload.get("max_results", 15))
        region_code = str(payload.get("country", "KR")).upper()
        policy_actions = payload.get("safety_policy")
        per_source_limit = self._resolve_collection_limit(payload, default_limit=25)

        source_docs = self.web_collector.collect(max_articles_per_source=per_source_limit, lookback_days=lookback_days)
        documents = [doc for docs in source_docs.values() for doc in docs]
        site_slangs = extract_meme_candidates(documents, top_k=max_results * 2)

        site_slang_risks: List[dict] = []
        blocked_terms: List[str] = []
        risk_flags: List[str] = []
        for slang in site_slangs:
            risk = analyze_text_risk(slang.get("keyword", ""), policy_actions=policy_actions)
            item = dict(slang)
            item["risk_flags"] = risk["risk_flags"]
            item["risk_score"] = risk["risk_score"]
            item["blocked_terms"] = risk["blocked_terms"]
            site_slang_risks.append(item)
            blocked_terms.extend(risk["blocked_terms"])
            risk_flags.extend(risk["risk_flags"])

        site_slang_risks.sort(key=lambda x: (x.get("risk_score", 0), x.get("meme_score", 0)), reverse=True)
        site_slang_risks = site_slang_risks[:max_results]

        youtube_docs = self.youtube_collector.collect_trending(max_results=30, region_code=region_code)
        youtube_keywords = extract_meme_candidates(youtube_docs, top_k=max_results * 2)
        youtube_rising = self._apply_growth(youtube_keywords, max_results=max_results)

        return {
            "schema_version": "v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "window_days": lookback_days,
            "source_health": {
                "wepick": "ok" if source_docs.get("wepick") else "empty",
                "gogumafarm": "ok" if source_docs.get("gogumafarm") else "empty",
                "careet": "ok" if source_docs.get("careet") else "empty",
                "youtube": "ok" if youtube_docs else "empty",
            },
            "site_slang_risks": site_slang_risks,
            "youtube_rising_keywords": youtube_rising,
            "blocked_terms": sorted(set(blocked_terms)),
            "risk_flags": sorted(set(risk_flags)),
            "safety_policy_applied": policy_actions or {},
            "final_summary": self._build_final_summary(site_slang_risks, youtube_rising),
        }

    def generate_keyword_summary(self, payload: dict) -> dict:
        policy_actions = payload.get("safety_policy")
        lookback_days = int(payload.get("lookback_days", 90))
        include_youtube = bool(payload.get("include_youtube", True))
        region_code = str(payload.get("country", "KR")).upper()
        max_keywords = int(payload.get("max_keywords", 5))
        max_contents_per_keyword = int(payload.get("max_contents_per_keyword", 3))
        per_source_limit = self._resolve_collection_limit(payload, default_limit=30)

        raw_keywords = payload.get("keywords", [])
        if not isinstance(raw_keywords, list):
            raw_keywords = []

        fallback = str(payload.get("input_keyword", "")).strip()
        if not raw_keywords and fallback:
            raw_keywords = [fallback]

        dedup_keywords: List[str] = []
        seen = set()
        for keyword in raw_keywords:
            text = str(keyword).strip()
            if not text:
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            dedup_keywords.append(text)

        dedup_keywords = dedup_keywords[:max_keywords]

        source_docs = self.web_collector.collect(max_articles_per_source=per_source_limit, lookback_days=lookback_days)
        web_contents = [doc for docs in source_docs.values() for doc in docs]

        summaries: List[dict] = []
        global_blocked_terms: List[str] = []
        global_risk_flags: List[str] = []

        for keyword in dedup_keywords:
            expanded = expand_keyword(keyword)

            yt_contents: List[dict] = []
            if include_youtube:
                yt_contents = self.youtube_collector.collect_related(
                    keyword,
                    max_results=12,
                    region_code=region_code,
                )

            combined_contents = web_contents + yt_contents
            scored = score_related_content(combined_contents, expanded)
            safe_contents, safety_summary = evaluate_contents_safety(
                scored,
                policy_actions=policy_actions,
            )

            top_contents = []
            for item in safe_contents[:max_contents_per_keyword]:
                top_contents.append(
                    {
                        "source": item.get("source", ""),
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content_score": item.get("content_score", 0),
                        "risk_score": item.get("risk_score", 0),
                        "risk_flags": item.get("risk_flags", []),
                    }
                )

            matched_web = score_related_content(web_contents, expanded)
            matched_web_docs = [doc for doc in matched_web if float(doc.get("relevance_score", 0)) > 0][:12]
            slang_candidates = extract_meme_candidates(matched_web_docs, top_k=5) if matched_web_docs else []

            site_slang_risks: List[dict] = []
            for slang in slang_candidates:
                risk = analyze_text_risk(slang.get("keyword", ""), policy_actions=policy_actions)
                site_slang_risks.append(
                    {
                        "keyword": slang.get("keyword", ""),
                        "meme_score": slang.get("meme_score", 0),
                        "risk_score": risk.get("risk_score", 0),
                        "risk_flags": risk.get("risk_flags", []),
                    }
                )

            site_slang_risks.sort(key=lambda x: (x.get("risk_score", 0), x.get("meme_score", 0)), reverse=True)

            trend_signal_score = 0.0
            if top_contents:
                trend_signal_score = round(
                    sum(float(x.get("content_score", 0)) for x in top_contents) / len(top_contents),
                    2,
                )

            summaries.append(
                {
                    "keyword": keyword,
                    "normalized_keywords": expanded,
                    "trend_signal_score": trend_signal_score,
                    "site_slang_risks": site_slang_risks[:3],
                    "top_contents": top_contents,
                    "blocked_terms": safety_summary.get("blocked_terms", []),
                    "risk_flags": safety_summary.get("risk_flags", []),
                    "safe_copy_suggestion": safe_copy_suggestion(f"{keyword} promotion summary"),
                }
            )

            global_blocked_terms.extend(safety_summary.get("blocked_terms", []))
            global_risk_flags.extend(safety_summary.get("risk_flags", []))

        return {
            "schema_version": "v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "window_days": lookback_days,
            "source_health": {
                "wepick": "ok" if source_docs.get("wepick") else "empty",
                "gogumafarm": "ok" if source_docs.get("gogumafarm") else "empty",
                "careet": "ok" if source_docs.get("careet") else "empty",
                "youtube": "disabled" if not include_youtube else "ok",
            },
            "keyword_summaries": summaries,
            "blocked_terms": sorted(set(global_blocked_terms)),
            "risk_flags": sorted(set(global_risk_flags)),
            "safety_policy_applied": policy_actions or {},
        }

    def _resolve_collection_limit(self, payload: dict, default_limit: int) -> Optional[int]:
        if bool(payload.get("collect_all_recent", False)):
            return None
        raw = payload.get("max_articles_per_source", default_limit)
        try:
            parsed = int(raw)
        except (TypeError, ValueError):
            return default_limit
        if parsed <= 0:
            return None
        return parsed

    def _apply_growth(self, current_keywords: List[dict], max_results: int) -> List[dict]:
        prev_scores = self._load_snapshot(self._snapshot_path)
        current_scores = {item.get("keyword", ""): float(item.get("meme_score", 0.0)) for item in current_keywords}

        rising_items: List[dict] = []
        for item in current_keywords:
            keyword = item.get("keyword", "")
            if not keyword:
                continue
            current_score = float(item.get("meme_score", 0.0))
            prev_score = float(prev_scores.get(keyword, 0.0))
            delta = current_score - prev_score
            if prev_score > 0:
                growth_pct = (delta / prev_score) * 100.0
            else:
                growth_pct = 100.0 if current_score > 0 else 0.0

            enriched = dict(item)
            enriched["previous_score"] = round(prev_score, 2)
            enriched["delta_score"] = round(delta, 2)
            enriched["growth_rate_pct"] = round(growth_pct, 2)
            rising_items.append(enriched)

        rising_items.sort(key=lambda x: (x.get("delta_score", 0), x.get("meme_score", 0)), reverse=True)
        self._save_snapshot(self._snapshot_path, current_scores)
        return rising_items[:max_results]

    def _load_keyword_snapshot(self) -> Dict[str, float]:
        return self._load_snapshot(self._snapshot_path)

    def _save_keyword_snapshot(self, snapshot: Dict[str, float]) -> None:
        self._save_snapshot(self._snapshot_path, snapshot)

    def _load_snapshot(self, snapshot_path: Path) -> Dict[str, float]:
        try:
            if snapshot_path.exists():
                with snapshot_path.open("r", encoding="utf-8") as fp:
                    raw = json.load(fp)
                if isinstance(raw, dict):
                    return {str(k): float(v) for k, v in raw.items()}
        except (OSError, ValueError):
            return {}
        return {}

    def _save_snapshot(self, snapshot_path: Path, snapshot: Dict[str, float]) -> None:
        try:
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            with snapshot_path.open("w", encoding="utf-8") as fp:
                json.dump(snapshot, fp, ensure_ascii=False, indent=2)
        except OSError:
            return

    def _build_topic_clusters(self, documents: List[dict], meme_keywords: List[dict], max_topics: int) -> List[dict]:
        now = datetime.now(timezone.utc)
        prev_scores = self._load_snapshot(self._site_topic_snapshot_path)
        current_scores: Dict[str, float] = {}

        topic_clusters: List[dict] = []
        for item in meme_keywords:
            keyword = str(item.get("keyword", "")).strip()
            if not keyword:
                continue
            normalized_topic = self._normalize_topic_phrase(keyword)
            if self._is_low_signal_topic(normalized_topic):
                continue

            related_docs = self._find_related_documents(documents, normalized_topic)
            if not related_docs:
                continue

            base_score = float(item.get("meme_score", 0.0))
            prev_score = float(prev_scores.get(normalized_topic, 0.0))
            delta_score = base_score - prev_score
            growth_rate_pct = (delta_score / prev_score * 100.0) if prev_score > 0 else (100.0 if base_score > 0 else 0.0)
            current_scores[normalized_topic] = max(current_scores.get(normalized_topic, 0.0), base_score)

            recent_14d = 0
            source_set = set()
            last_seen: Optional[datetime] = None
            samples = []
            for doc in related_docs[:5]:
                source = str(doc.get("source", ""))
                if source:
                    source_set.add(source)

                published_dt = self._parse_iso_datetime(doc.get("published_at"))
                if published_dt and (now - published_dt).days <= 14:
                    recent_14d += 1
                if published_dt and (last_seen is None or published_dt > last_seen):
                    last_seen = published_dt

                samples.append(
                    {
                        "source": source,
                        "title": doc.get("title", ""),
                        "url": doc.get("url", ""),
                        "published_at": doc.get("published_at", ""),
                        "excerpt": self._short_text(str(doc.get("excerpt", "")), 180),
                    }
                )

            surge_boost = max(0.0, min(20.0, (delta_score * 0.6) + (recent_14d * 1.5) + (max(len(source_set) - 1, 0) * 2.0)))
            topic_score = min(100.0, base_score + surge_boost)
            recency_weight = self._recency_weight_from_last_seen(last_seen)
            weighted_topic_score = min(100.0, topic_score * recency_weight)

            topic_clusters.append(
                {
                    "topic": normalized_topic,
                    "topic_score": round(topic_score, 2),
                    "weighted_topic_score": round(weighted_topic_score, 2),
                    "recency_weight": round(recency_weight, 3),
                    "base_score": round(base_score, 2),
                    "surge_boost": round(surge_boost, 2),
                    "delta_score": round(delta_score, 2),
                    "growth_rate_pct": round(growth_rate_pct, 2),
                    "evidence_count": len(related_docs),
                    "recent_14d_count": recent_14d,
                    "source_coverage": sorted(source_set),
                    "last_seen_at": last_seen.isoformat() if last_seen else "",
                    "summary": self._summarize_documents(related_docs),
                    "sample_contents": samples,
                }
            )

        topic_clusters = self._merge_topic_clusters(topic_clusters)
        topic_clusters.sort(
            key=lambda x: (
                x.get("weighted_topic_score", x.get("topic_score", 0)),
                x.get("recent_14d_count", 0),
                x.get("topic_score", 0),
            ),
            reverse=True,
        )
        self._save_snapshot(self._site_topic_snapshot_path, current_scores)
        return topic_clusters[:max_topics]

    def _find_related_documents(self, documents: List[dict], keyword: str) -> List[dict]:
        target = keyword.lower().strip()
        target_tokens = set(tokenize(target))
        if not target_tokens:
            return []

        related: List[dict] = []
        for doc in documents:
            text = " ".join(
                [
                    str(doc.get("clean_title") or doc.get("title", "")),
                    str(doc.get("clean_excerpt") or doc.get("excerpt", "")),
                    str(doc.get("clean_body_text") or doc.get("body_text", "")),
                    str(doc.get("clean_emphasis_text") or doc.get("emphasis_text", "")),
                ]
            ).lower()
            text_tokens = set(tokenize(text))
            if target in text or target_tokens.intersection(text_tokens):
                related.append(doc)

        related.sort(
            key=lambda d: self._parse_iso_datetime(d.get("published_at")) or datetime(1970, 1, 1, tzinfo=timezone.utc),
            reverse=True,
        )
        return related

    def _summarize_documents(self, documents: List[dict], max_sentences: int = 3) -> str:
        emphasis_terms: List[str] = []
        seen_emphasis = set()
        for doc in documents[:8]:
            emphasis = str(doc.get("clean_emphasis_text") or doc.get("emphasis_text", "")).strip()
            if not emphasis:
                continue
            for token in emphasis.split():
                if len(token) < 2:
                    continue
                if token in seen_emphasis:
                    continue
                seen_emphasis.add(token)
                emphasis_terms.append(token)
                if len(emphasis_terms) >= 6:
                    break
            if len(emphasis_terms) >= 6:
                break

        sentences: List[str] = []
        for doc in documents[:8]:
            text = " ".join(
                [
                    str(doc.get("clean_excerpt") or doc.get("excerpt", "")),
                    str(doc.get("clean_body_text") or doc.get("body_text", "")),
                    str(doc.get("clean_emphasis_text") or doc.get("emphasis_text", "")),
                ]
            ).strip()
            if not text:
                continue
            chunks = re.split(r"(?<=[.!?])\s+|\n+", text)
            for chunk in chunks:
                cleaned = chunk.strip()
                if len(cleaned) < 30:
                    continue
                if cleaned in sentences:
                    continue
                if "트렌드를 읽는 가장 빠른 방법" in cleaned:
                    continue
                sentences.append(cleaned)
                if len(sentences) >= max_sentences:
                    break

        summary_parts: List[str] = []
        if emphasis_terms:
            summary_parts.append("핵심표현: " + ", ".join(emphasis_terms[:6]))
        if sentences:
            summary_parts.append(" ".join(sentences))
        return " ".join(summary_parts)

    def _normalize_topic_phrase(self, topic: str) -> str:
        tokens = [t for t in tokenize(topic.lower()) if t and t not in TOPIC_FUNCTION_WORDS]
        if not tokens:
            return ""

        for idx, token in enumerate(tokens):
            if token in TOPIC_CUE_TERMS or any(token.endswith(cue) for cue in TOPIC_CUE_TERMS):
                start = max(0, idx - 1)
                return " ".join(tokens[start : idx + 1])

        if len(tokens) >= 2:
            return " ".join(tokens[:2])
        return tokens[0]

    def _is_low_signal_topic(self, topic: str) -> bool:
        norm = (topic or "").strip().lower()
        if not norm:
            return True
        if norm in GENERIC_TOPIC_BLACKLIST:
            return True
        if any(site in norm for site in ("고구마팜", "careet", "wepick", "캐릿", "위픽")):
            return True
        if norm in TOPIC_FUNCTION_WORDS:
            return True
        if norm.isdigit():
            return True
        if re.search(r"20\d{2}\s*년?\s*\d{1,2}\s*월", norm):
            return True
        return False

    def _merge_topic_clusters(self, clusters: List[dict]) -> List[dict]:
        merged: Dict[str, dict] = {}
        for cluster in clusters:
            topic = str(cluster.get("topic", "")).strip()
            if not topic:
                continue

            if topic not in merged:
                merged[topic] = dict(cluster)
                continue

            cur = merged[topic]
            cur["topic_score"] = round(max(float(cur.get("topic_score", 0)), float(cluster.get("topic_score", 0))), 2)
            cur["base_score"] = round(max(float(cur.get("base_score", 0)), float(cluster.get("base_score", 0))), 2)
            cur["surge_boost"] = round(max(float(cur.get("surge_boost", 0)), float(cluster.get("surge_boost", 0))), 2)
            cur["delta_score"] = round(max(float(cur.get("delta_score", 0)), float(cluster.get("delta_score", 0))), 2)
            cur["growth_rate_pct"] = round(max(float(cur.get("growth_rate_pct", 0)), float(cluster.get("growth_rate_pct", 0))), 2)
            cur["evidence_count"] = int(cur.get("evidence_count", 0)) + int(cluster.get("evidence_count", 0))
            cur["recent_14d_count"] = int(cur.get("recent_14d_count", 0)) + int(cluster.get("recent_14d_count", 0))

            src_union = set(cur.get("source_coverage", [])) | set(cluster.get("source_coverage", []))
            cur["source_coverage"] = sorted(src_union)

            cur_last = self._parse_iso_datetime(cur.get("last_seen_at"))
            new_last = self._parse_iso_datetime(cluster.get("last_seen_at"))
            if new_last and (not cur_last or new_last > cur_last):
                cur["last_seen_at"] = new_last.isoformat()

            merged_samples = list(cur.get("sample_contents", [])) + list(cluster.get("sample_contents", []))
            dedup_samples: List[dict] = []
            seen_urls = set()
            for sample in merged_samples:
                url = str(sample.get("url", ""))
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                dedup_samples.append(sample)
                if len(dedup_samples) >= 5:
                    break
            cur["sample_contents"] = dedup_samples

            cur_summary = str(cur.get("summary", ""))
            new_summary = str(cluster.get("summary", ""))
            if len(new_summary) > len(cur_summary):
                cur["summary"] = new_summary

        return list(merged.values())

    def _build_ad_candidate_keywords(self, topic_clusters: List[dict], max_keywords: int = 10) -> List[dict]:
        candidates: List[dict] = []
        for item in topic_clusters:
            topic = str(item.get("topic", "")).strip()
            accepted, reason = self._is_marketing_usable_trend_keyword(topic, item)
            if not accepted:
                continue
            candidates.append(
                {
                    "keyword": topic,
                    "topic_score": item.get("topic_score", 0),
                    "weighted_topic_score": item.get("weighted_topic_score", item.get("topic_score", 0)),
                    "recency_weight": item.get("recency_weight", 1.0),
                    "growth_rate_pct": item.get("growth_rate_pct", 0),
                    "source_coverage": item.get("source_coverage", []),
                    "confidence": self._trend_keyword_confidence(topic, item),
                    "selection_reason": reason,
                }
            )

        candidates.sort(
            key=lambda x: (
                x.get("weighted_topic_score", x.get("topic_score", 0)),
                x.get("growth_rate_pct", 0),
                x.get("topic_score", 0),
            ),
            reverse=True,
        )
        return candidates[:max_keywords]

    def _recency_weight_from_last_seen(self, last_seen: Optional[datetime]) -> float:
        if not last_seen:
            return 1.0
        now = datetime.now(timezone.utc)
        days = max(0.0, (now - last_seen).total_seconds() / 86400.0)
        if days <= 7:
            return 1.35
        if days <= 30:
            return 1.2
        if days <= 90:
            return 1.08
        return 1.0

    def _build_trend_keyword_quality(self, topic_clusters: List[dict]) -> Dict[str, object]:
        rejected_reasons: Dict[str, int] = {}
        accepted_count = 0
        for item in topic_clusters:
            topic = str(item.get("topic", "")).strip()
            accepted, reason = self._is_marketing_usable_trend_keyword(topic, item)
            if accepted:
                accepted_count += 1
                continue
            rejected_reasons[reason] = rejected_reasons.get(reason, 0) + 1

        return {
            "total_topics": len(topic_clusters),
            "accepted_topics": accepted_count,
            "rejected_topics": max(len(topic_clusters) - accepted_count, 0),
            "rejected_reason_counts": rejected_reasons,
        }

    def _is_marketing_usable_trend_keyword(self, keyword: str, topic_item: dict) -> tuple[bool, str]:
        norm = (keyword or "").strip().lower()
        if not norm:
            return False, "empty"
        if self._is_low_signal_topic(norm):
            return False, "low_signal"
        if norm in GENERIC_AD_BLOCKLIST:
            return False, "generic"
        if re.search(r"20\d{2}\s*년?\s*\d{1,2}\s*월", norm):
            return False, "date_like"
        if norm.isdigit() or re.fullmatch(r"20\d{2}년?", norm):
            return False, "year_or_numeric"

        tokens = norm.split()
        token_count = len(tokens)
        cue_hit = any(cue in norm for cue in TOPIC_CUE_TERMS)
        score = float(topic_item.get("topic_score", 0))

        if any(token in PHRASE_NOISE_TOKENS for token in tokens):
            return False, "phrase_noise"
        if token_count >= 2 and any(token.endswith(("은", "는", "이", "가", "을", "를")) for token in tokens):
            return False, "particle_phrase"

        if token_count == 1 and not cue_hit:
            return False, "single_non_cue"
        if score < 45:
            return False, "low_score"

        if cue_hit and score >= 45:
            return True, "cue_term"
        if token_count >= 2 and score >= 50:
            return True, "multiword_phrase"
        return False, "insufficient_signal"

    def _trend_keyword_confidence(self, keyword: str, topic_item: dict) -> float:
        score = float(topic_item.get("topic_score", 0))
        growth = float(topic_item.get("growth_rate_pct", 0))
        sources = len(topic_item.get("source_coverage", []))
        cue_bonus = 8.0 if any(cue in keyword for cue in TOPIC_CUE_TERMS) else 0.0
        source_bonus = min(10.0, max(0.0, (sources - 1) * 5.0))
        growth_bonus = min(8.0, max(0.0, growth / 20.0))
        confidence = min(100.0, max(0.0, score * 0.75 + cue_bonus + source_bonus + growth_bonus))
        return round(confidence, 2)

    def _parse_iso_datetime(self, value) -> Optional[datetime]:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            return None

    def _short_text(self, text: str, max_len: int) -> str:
        cleaned = " ".join((text or "").split())
        if len(cleaned) <= max_len:
            return cleaned
        return cleaned[: max_len - 3] + "..."

    def _build_final_summary(self, site_slang_risks: List[dict], youtube_rising: List[dict]) -> Dict[str, object]:
        top_risky = [item for item in site_slang_risks if item.get("risk_score", 0) > 0][:5]
        top_rising = youtube_rising[:5]

        return {
            "site_risk_keywords": [item.get("keyword", "") for item in top_risky],
            "youtube_rising_keywords": [item.get("keyword", "") for item in top_rising],
            "notes": [
                "Site slang risk list is sorted by risk score and meme score.",
                "YouTube rising keywords are ranked by score delta compared to the previous snapshot.",
            ],
        }

    def _build_card_event_insights(self, keyword: str, contents: List[dict]) -> Dict[str, object]:
        top_terms: Dict[str, int] = {}
        for item in contents[:10]:
            for term in item.get("matched_terms", []):
                top_terms[term] = top_terms.get(term, 0) + 1

        sorted_terms = sorted(top_terms.items(), key=lambda x: x[1], reverse=True)
        top_theme = sorted_terms[0][0] if sorted_terms else keyword

        return {
            "top_theme": top_theme,
            "recommended_angles": [
                "comparison format for billing discount versus instant discount",
                "short campaign with limited-time benefit framing",
            ],
            "copy_seed": [
                f"{keyword} this month, where is the biggest real discount",
                f"{keyword} benefit summary in one view",
            ],
        }
