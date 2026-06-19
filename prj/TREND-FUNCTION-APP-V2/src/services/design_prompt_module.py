from __future__ import annotations

from typing import Any, Dict, List

from src.services.design_prompt_builder import DesignPromptBuilder


class DesignPromptModule:
    """Function-app style module entrypoint for design prompt generation."""

    def __init__(self) -> None:
        self.builder = DesignPromptBuilder()

    def generate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._normalize_payload(payload or {})
        return self.builder.generate(normalized)

    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Backward compatibility: support both old and new field names.
        event_summary = payload.get("event_summary")
        if event_summary is None:
            event_summary = payload.get("realtime_keyword_summary", "")

        trend_summary = payload.get("trend_summary")
        if trend_summary is None:
            trend_summary = payload.get("trend_memes", [])

        primary = payload.get("primary_keywords") or {}
        if not isinstance(primary, dict):
            primary = {}

        return {
            "primary_keywords": {
                "targets": self._ensure_list(primary.get("targets")),
                "benefits": self._ensure_list(primary.get("benefits")),
                "conditions": self._ensure_list(primary.get("conditions")),
            },
            "free_input": payload.get("free_input", ""),
            "event_summary": event_summary or "",
            "trend_summary": self._ensure_list(trend_summary),
            "review_feedback": payload.get("review_feedback", ""),
            "previous_prompt": payload.get("previous_prompt", ""),
            "prompt_only": bool(payload.get("prompt_only", False)),
        }

    def _ensure_list(self, value: Any) -> List[str]:
        if isinstance(value, list):
            return [str(v) for v in value if str(v).strip()]
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return []
