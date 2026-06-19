from __future__ import annotations

import json
import os
from typing import Dict, Tuple

import requests


class LLMPromptSynthesizer:
    def synthesize(self, context: Dict[str, object]) -> Tuple[str, Dict[str, object]]:
        """LLM에 입력값을 보내 이미지 생성 프롬프트를 생성합니다."""
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            return "", {"enabled": False, "used": False, "reason": "missing_openai_api_key"}

        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        model = os.getenv("OPENAI_MODEL", "gpt-4o").strip() or "gpt-4o"
        timeout = self._safe_timeout_seconds(os.getenv("LLM_TIMEOUT_SECONDS", "25"))
        is_azure = "openai.azure.com" in base_url or "cognitiveservices.azure.com" in base_url
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")

        system_message = "You are a professional Korean ad design prompt writer. Generate creative, practical image generation prompts."
        user_message = json.dumps({
            "task": "Generate a Korean image generation prompt from user inputs",
            "requirements": [
                "Create one comprehensive prompt that synthesizes all inputs",
                "Include all targets, benefits, conditions, and trend memes",
                "Make it practical for image generation",
                "Reflect user feedback if provided",
                "Output only the prompt text, no markdown or code fences",
            ],
            "context": context,
        }, ensure_ascii=False)

        # Azure/OpenAI 공통: chat/completions 사용
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
        }

        try:
            headers = {"Content-Type": "application/json"}
            if is_azure:
                headers["api-key"] = api_key
                url = f"{base_url}/openai/deployments/{model}/chat/completions?api-version={api_version}"
            else:
                headers["Authorization"] = f"Bearer {api_key}"
                url = f"{base_url}/chat/completions"

            response = requests.post(url, headers=headers, json=body, timeout=timeout)
            response.raise_for_status()
            parsed = response.json()
            final_prompt = self._extract_chat_completion(parsed)
            if not final_prompt:
                return "", {
                    "enabled": True,
                    "used": False,
                    "reason": "empty_llm_response",
                    "model": model,
                }

            return final_prompt, {
                "enabled": True,
                "used": True,
                "model": model,
            }
        except Exception as exc:
            import traceback
            return "", {
                "enabled": True,
                "used": False,
                "reason": f"llm_error:{type(exc).__name__}:{exc}",
                "model": model,
                "traceback": traceback.format_exc(),
            }

    def _extract_chat_completion(self, parsed: Dict[str, object]) -> str:
        """chat/completions 응답에서 메시지 텍스트를 추출합니다."""
        try:
            content = parsed["choices"][0]["message"]["content"]
            if isinstance(content, str):
                return content.strip()
        except (KeyError, IndexError, TypeError):
            pass
        return ""

    def _safe_timeout_seconds(self, raw: str) -> float:
        """타임아웃 값을 5-60초 범위로 정규화합니다."""
        try:
            value = float(raw)
            return max(5.0, min(value, 60.0))
        except (TypeError, ValueError):
            return 25.0