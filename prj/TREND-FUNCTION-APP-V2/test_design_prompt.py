#!/usr/bin/env python3
"""Design Prompt Builder 테스트 스크립트."""

import json
import sys
from src.services.design_prompt_builder import DesignPromptBuilder

sample_payload = {
    "primary_keywords": {
        "targets": ["신용카드", "체크카드"],
        "benefits": ["캐시백", "현장할인"],
        "conditions": ["건당 10만원 이상", "월 1회 응모"]
    },
    "free_input": "여름 시즌, 밝고 활기찬 분위기, 나침반 이미지 필수",
    "event_summary": "고물가 시대 생활밀착 할인, 여름 여행 수요 증가",
    "trend_summary": ["거제 야호"],
    "review_feedback": "",
    "prompt_only": True
}

if __name__ == "__main__":
    print("=" * 80)
    print("Design Prompt Builder 테스트")
    print("=" * 80)
    print("\n입력값:")
    print(json.dumps(sample_payload, indent=2, ensure_ascii=False))
    print("\n처리 중...")
    builder = DesignPromptBuilder()
    result = builder.generate(sample_payload)
    print("\n출력값:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("\n생성된 프롬프트:")
    print(result.get("prompt", "N/A"))
    print("\nLLM 상태:", result.get("llm", {}))