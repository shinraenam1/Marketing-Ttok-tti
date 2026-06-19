from __future__ import annotations

import re
import os
from datetime import datetime, timezone
from typing import Dict, List

from src.services.llm_prompt_synthesizer import LLMPromptSynthesizer


class DesignPromptBuilder:
    def __init__(self):
        self.llm_synthesizer = LLMPromptSynthesizer()

    def generate(self, payload: dict) -> dict:
        primary = payload.get("primary_keywords") or {}
        user_input = self._clean_text(payload.get("free_input", ""))
        event_summary = self._clean_text(payload.get("event_summary", ""))
        trend_summary = self._normalize_list(payload.get("trend_summary"))
        review_feedback = self._clean_text(payload.get("review_feedback", ""))
        previous_prompt = self._clean_text(payload.get("previous_prompt", ""))

        targets = self._normalize_list(primary.get("targets"))
        benefits = self._normalize_list(primary.get("benefits"))
        conditions = self._normalize_list(primary.get("conditions"))

        # LLM으로 프롬프트 생성
        llm_prompt, llm_meta = self.llm_synthesizer.synthesize(
            self._build_llm_context(
                targets=targets,
                benefits=benefits,
                conditions=conditions,
                trend_summary=trend_summary,
                free_input=user_input,
                event_summary=event_summary,
                review_feedback=review_feedback,
                previous_prompt=previous_prompt,
            )
        )

        # LLM 실패 시 규칙 기반 fallback
        final_prompt = llm_prompt
        if not llm_prompt:
            offer_rules = self._extract_offer_rules(user_input)
            extracted = self._extract_context(
                user_input=user_input,
                event_summary=event_summary,
                targets=targets,
                benefits=benefits,
                conditions=conditions,
                trend_summary=trend_summary,
                offer_rules=offer_rules,
            )
            final_prompt = self._build_image_generation_prompt(
                targets=targets,
                benefits=benefits,
                conditions=conditions,
                offer_rules=offer_rules,
                trend_summary=trend_summary,
                extracted=extracted,
                user_input=user_input,
                event_summary=event_summary,
            )
            llm_meta["used"] = False
            llm_meta["reason"] = "using_fallback_rule_based"

        prompt_only = bool(payload.get("prompt_only", False))
        if prompt_only:
            return {
                "schema_version": "v1",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "prompt": final_prompt,
                "llm": llm_meta,
            }

        return {
            "schema_version": "v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "prompt": final_prompt,
            "inputs": {
                "targets": targets,
                "benefits": benefits,
                "conditions": conditions,
                "free_input": user_input,
                "event_summary": event_summary,
                "trend_summary": trend_summary,
                "review_feedback": review_feedback,
            },
            "llm": llm_meta,
        }

    def _build_llm_context(
        self,
        targets: List[str],
        benefits: List[str],
        conditions: List[str],
        trend_summary: List[str],
        free_input: str,
        event_summary: str,
        review_feedback: str,
        previous_prompt: str,
    ) -> Dict[str, object]:
        """입력값을 LLM에 보내 이미지 생성 프롬프트를 생성하도록 합니다."""
        return {
            "task": "generate_image_prompt",
            "inputs": {
                "targets": targets,
                "benefits": benefits,
                "conditions": conditions,
                "trend_summary": trend_summary,
                "free_input": free_input,
                "event_summary": event_summary,
            },
            "feedback": review_feedback or None,
            "previous_prompt": previous_prompt or None,
        }

    def _build_image_generation_prompt(
        self,
        targets: List[str],
        benefits: List[str],
        conditions: List[str],
        offer_rules: List[str],
        trend_summary: List[str],
        extracted: Dict[str, object],
        user_input: str,
        event_summary: str,
    ) -> str:
        """규칙 기반 fallback 프롬프트 생성."""
        target_text = ", ".join(targets) if targets else "카드 고객"
        merged_benefits = self._merge_unique(benefits if benefits else ["할인 혜택"], offer_rules)
        merged_conditions = self._merge_unique(conditions if conditions else ["이벤트 조건"], offer_rules)
        benefit_text = ", ".join(merged_benefits)
        condition_text = ", ".join(merged_conditions)
        objects = extracted.get("required_objects") or ["카드"]
        object_text = ", ".join(objects)
        scene_text = ", ".join(extracted.get("scene_keywords") or ["브랜드 프로모션 배경"])
        tone_text = ", ".join(extracted.get("tone_keywords") or ["명확함", "가독성"])
        campaign_theme = str(extracted.get("campaign_theme", "타겟 맞춤 프로모션"))
        mood = str(extracted.get("customer_mood", "고객 관점 가치 전달"))
        meme_text = ", ".join(trend_summary) if trend_summary else "없음"

        return (
            f"상업용 프로모션 포스터/배너 디자인. 배경 장면은 {scene_text}. "
            f"중앙 메인에는 {object_text}를 배치해 '{campaign_theme}' 메시지를 시각적으로 전달. "
            f"대상 고객은 {target_text}. 혜택({benefit_text})은 카드 주변 배지/아이콘으로 직관적으로 노출하고, "
            f"조건({condition_text})은 하단 인포그래픽 영역에서 깔끔하게 정리. "
            f"반드시 노출할 제공조건: {condition_text}. "
            f"트렌드 반영 키워드: {meme_text}. "
            f"전체 분위기는 {mood} 중심이며 톤앤매너는 {tone_text}. "
            "메시지 중심 레이아웃, 과도한 장식 최소화, 브랜드 광고 퀄리티. "
            f"추가 의도 반영: {user_input or '없음'}. "
            f"이벤트 맥락 반영: {event_summary or '없음'}."
        )

    def _extract_context(
        self,
        user_input: str,
        event_summary: str,
        targets: List[str],
        benefits: List[str],
        conditions: List[str],
        trend_summary: List[str],
        offer_rules: List[str],
    ) -> Dict[str, object]:
        full_text = f"{user_input} {event_summary} {' '.join(trend_summary)}".strip()
        required_objects = self._extract_required_objects(user_input, targets)
        seasonality = self._extract_seasonality(full_text)
        detected_topics = self._extract_topic_keywords(full_text)
        if trend_summary:
            detected_topics = self._merge_unique(detected_topics, ["밈"])
        campaign_theme = self._build_campaign_theme(detected_topics, benefits)
        customer_mood = self._build_customer_mood(full_text)
        tone_keywords = self._extract_tone_keywords(full_text)
        scene_keywords = self._build_scene_keywords(seasonality, detected_topics)
        if trend_summary:
            scene_keywords = self._merge_unique(scene_keywords, [f"트렌드 포인트: {', '.join(trend_summary[:3])}"])

        if conditions or offer_rules:
            campaign_theme = f"{campaign_theme} · 조건형 혜택 안내"
        if trend_summary:
            campaign_theme = f"{campaign_theme} · 밈 키워드 연계"

        return {
            "campaign_theme": campaign_theme,
            "required_objects": required_objects,
            "seasonality": seasonality,
            "customer_mood": customer_mood,
            "tone_keywords": tone_keywords,
            "scene_keywords": scene_keywords,
        }

    def _extract_required_objects(self, user_input: str, targets: List[str]) -> List[str]:
        objects: List[str] = []
        if any("카드" in target for target in targets):
            objects.append("카드")
        if "나침반" in user_input:
            objects.append("나침반")
        return self._merge_unique([], objects or ["핵심 오브젝트"])

    def _extract_seasonality(self, text: str) -> str:
        seasons = [s for s in ["봄", "여름", "가을", "겨울"] if s in text]
        if not seasons:
            return "시즌 중립"
        return ", ".join(seasons)

    def _extract_topic_keywords(self, text: str) -> List[str]:
        topic_map = {
            "여행": ["여행", "호텔", "숙박", "항공"],
            "교육": ["교육", "입시", "학습"],
            "생활밀착": ["생활", "생활밀착", "마트", "슈퍼"],
            "쇼핑": ["쇼핑", "구매", "결제"],
            "금융": ["카드", "캐시백", "할인"],
        }
        topics: List[str] = []
        for topic, signals in topic_map.items():
            if any(signal in text for signal in signals):
                topics.append(topic)
        return self._merge_unique([], topics)

    def _build_campaign_theme(self, topics: List[str], benefits: List[str]) -> str:
        topic_part = ", ".join(topics) if topics else "타겟 맞춤"
        benefit_part = "혜택 강조" if benefits else "정보 전달"
        return f"{topic_part} 중심 {benefit_part} 프로모션"

    def _build_customer_mood(self, text: str) -> str:
        if any(token in text for token in ["고물가", "고유가", "부담", "절약"]):
            return "부담 완화와 실속 소비"
        if any(token in text for token in ["프리미엄", "고급", "럭셔리"]):
            return "프리미엄 가치와 만족감"
        return "혜택 체감과 참여 동기 강화"

    def _extract_tone_keywords(self, text: str) -> List[str]:
        tone_map = {
            "밝음": ["밝", "산뜻", "경쾌"],
            "신뢰감": ["신뢰", "안정", "확실"],
            "프리미엄": ["프리미엄", "고급", "세련"],
            "활동적": ["활기", "액티브", "에너지"],
            "친근함": ["친근", "편안", "일상"],
        }
        tones: List[str] = []
        for tone, signals in tone_map.items():
            if any(signal in text for signal in signals):
                tones.append(tone)
        return self._merge_unique([], tones or ["명확함", "가독성"])

    def _build_scene_keywords(self, seasonality: str, topics: List[str]) -> List[str]:
        scenes: List[str] = []
        if seasonality != "시즌 중립":
            scenes.append(f"{seasonality} 시즌감")
        if "여행" in topics:
            scenes.append("이동/여행 준비 맥락")
        if "교육" in topics:
            scenes.append("학습/진로 안내 맥락")
        if "생활밀착" in topics:
            scenes.append("일상 소비 맥락")
        return self._merge_unique([], scenes or ["프로모션 중심 스튜디오 배경"])

    def _extract_offer_rules(self, user_input: str) -> List[str]:
        if not user_input:
            return []
        rules: List[str] = []
        money_percent = re.compile(r"\d+\s*만원\s*이상\s*결제\s*시\s*\d+\s*%\s*할인")
        rules.extend(m.group(0).strip() for m in money_percent.finditer(user_input))
        money_fixed = re.compile(r"\d+\s*만원\s*이상\s*결제\s*시\s*\d+\s*(?:천원|만원|원)\s*할인")
        rules.extend(m.group(0).strip() for m in money_fixed.finditer(user_input))
        return self._merge_unique([], [" ".join(r.replace(",", " ").split()) for r in rules])

    def _merge_unique(self, base_items: List[str], extra_items: List[str]) -> List[str]:
        merged: List[str] = []
        seen = set()
        for item in [*(base_items or []), *(extra_items or [])]:
            text = self._clean_text(item)
            if not text or text in seen:
                continue
            seen.add(text)
            merged.append(text)
        return merged

    def _normalize_list(self, value: object) -> List[str]:
        if isinstance(value, list):
            raw = value
        elif isinstance(value, str):
            raw = [part.strip() for part in value.split(",")]
        else:
            raw = []
        result: List[str] = []
        seen = set()
        for item in raw:
            text = self._clean_text(item)
            if not text or text in seen:
                continue
            seen.add(text)
            result.append(text)
        return result

    def _clean_text(self, value: object) -> str:
        if not isinstance(value, str):
            return ""
        return " ".join(value.strip().split())
