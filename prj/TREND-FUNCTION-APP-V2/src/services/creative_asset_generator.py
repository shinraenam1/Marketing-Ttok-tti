from __future__ import annotations

import base64
import os
import time
from datetime import datetime, timezone
from typing import Dict

import requests


class CreativeAssetGenerator:
    def __init__(self) -> None:
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip() or os.getenv("AZURE_OPENAI_KEY", "").strip()
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip().rstrip("/")

        self.image_api_key = os.getenv("IMAGE_OPENAI_KEY", "").strip() or os.getenv("AZURE_OPENAI_KEY", "").strip() or self.openai_api_key
        self.image_endpoint = os.getenv("IMAGE_OPENAI_ENDPOINT", "").strip().rstrip("/") or self.azure_endpoint

        base_from_env = os.getenv("OPENAI_BASE_URL", "").strip().rstrip("/")
        if base_from_env:
            self.openai_base_url = base_from_env
        elif self.azure_endpoint:
            self.openai_base_url = f"{self.azure_endpoint}/openai/v1"
        else:
            self.openai_base_url = "https://api.openai.com/v1"

        if self.image_endpoint:
            self.image_base_url = f"{self.image_endpoint}/openai/v1"
        else:
            self.image_base_url = self.openai_base_url
        self.azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")

        self.image_model = (
            os.getenv("IMAGE_MODEL", "").strip()
            or os.getenv("AZURE_OPENAI_DEPLOYMENT", "").strip()
            or "gpt-image-2"
        )
        self.image_size = os.getenv("IMAGE_SIZE", "1024x1024").strip() or "1024x1024"
        self.image_quality = os.getenv("IMAGE_QUALITY", "low").strip() or "low"

        self.video_endpoint = os.getenv("AZURE_SORA_VIDEO_URL", "").strip().rstrip("/")
        if not self.video_endpoint and self.azure_endpoint:
            self.video_endpoint = f"{self.azure_endpoint}/openai/v1/videos"

        self.video_api_key = os.getenv("AZURE_OPENAI_API_KEY", "").strip() or self.openai_api_key
        self.video_model = os.getenv("AZURE_SORA_DEPLOYMENT", "sora-2").strip() or "sora-2"
        self.video_size = os.getenv("VIDEO_SIZE", "1280x720").strip() or "1280x720"
        self.video_seconds = os.getenv("VIDEO_SECONDS", "8").strip() or "8"
        self.video_timeout = int(os.getenv("VIDEO_TIMEOUT_SECONDS", "180"))
        self.video_poll_interval = int(os.getenv("VIDEO_POLL_INTERVAL_SECONDS", "3"))

    def generate(self, payload: dict) -> dict:
        prompt = str(payload.get("prompt", "")).strip()
        if not prompt:
            raise ValueError("prompt is required")

        video_prompt = self._build_video_prompt(prompt)

        include_image = bool(payload.get("include_image", True))
        include_video = bool(payload.get("include_video", True))

        result: Dict[str, object] = {
            "schema_version": "v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "prompt": prompt,
            "video_prompt": video_prompt,
            "image": None,
            "video": None,
            "errors": [],
        }

        if include_image:
            try:
                result["image"] = self._generate_image(prompt)
            except Exception as exc:
                result["errors"].append(f"image_error:{type(exc).__name__}:{exc}")

        if include_video:
            try:
                result["video"] = self._generate_video(video_prompt)
            except Exception as exc:
                result["errors"].append(f"video_error:{type(exc).__name__}:{exc}")

        return result

    def _build_video_prompt(self, prompt: str) -> str:
        """Keep the same campaign concept but enforce video-specific output instructions."""
        video_instructions = (
            "\n\n[VIDEO MODE]\n"
            "위 콘셉트와 메시지는 그대로 유지하고, 반드시 영상 광고용으로 제작하세요. "
            "영상길이 8초, 장면 전환이 있는 시네마틱 모션, 카메라 무빙, 텍스트 오버레이, "
            "브랜드 컬러 일관성, 마지막 1초 CTA 장면을 포함하세요."
        )
        return f"{prompt}{video_instructions}"

    def _is_azure_deployments_openai(self, base_url: str) -> bool:
        base = base_url.lower()
        if base.endswith("/openai/v1"):
            return False
        return "openai.azure.com" in base or "cognitiveservices.azure.com" in base

    def _is_foundry_openai(self, base_url: str) -> bool:
        base = base_url.lower()
        return "services.ai.azure.com" in base or base.endswith("/openai/v1")

    def _generate_image(self, prompt: str) -> dict:
        if not self.image_api_key:
            raise ValueError("IMAGE_OPENAI_KEY/AZURE_OPENAI_KEY/OPENAI_API_KEY is required for image generation")

        def _post_image_request(final_prompt: str) -> dict:
            body = {
                "prompt": final_prompt,
                "n": 1,
                "size": self.image_size,
                "quality": self.image_quality,
            }

            if self._is_azure_deployments_openai(self.image_base_url):
                url = f"{self.image_base_url}/openai/deployments/{self.image_model}/images/generations?api-version={self.azure_api_version}"
                headers = {
                    "Content-Type": "application/json",
                    "api-key": self.image_api_key,
                }
            elif self._is_foundry_openai(self.image_base_url) or self.image_base_url.endswith("/openai/v1"):
                url = f"{self.image_base_url}/images/generations"
                headers = {
                    "Content-Type": "application/json",
                    "api-key": self.image_api_key,
                }
                body["model"] = self.image_model
            else:
                url = f"{self.image_base_url}/images/generations"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.image_api_key}",
                }
                body["model"] = self.image_model

            response = requests.post(url, headers=headers, json=body, timeout=120)
            if response.status_code >= 400:
                raise RuntimeError(f"image_api_error:{response.status_code}:{response.text}")

            parsed = response.json()
            data_list = parsed.get("data") or []
            if not data_list:
                raise RuntimeError("image generation returned no data")

            b64 = data_list[0].get("b64_json")
            if not b64:
                raise RuntimeError("image generation response missing b64_json")

            return {
                "mime_type": "image/png",
                "data_url": f"data:image/png;base64,{b64}",
                "size": self.image_size,
                "model": self.image_model,
            }

        try:
            return _post_image_request(prompt)
        except RuntimeError as exc:
            if "moderation_blocked" not in str(exc):
                raise

            safe_prompt = (
                "A clean, family-safe Korean bank promotion poster with abstract financial growth icons, "
                "bright professional layout, no people, no sensitive content, no risky elements."
            )
            return _post_image_request(safe_prompt)

    def _generate_video(self, prompt: str) -> dict:
        if not self.video_endpoint:
            raise ValueError("AZURE_SORA_VIDEO_URL is required for video generation")
        if not self.video_api_key:
            raise ValueError("AZURE_OPENAI_API_KEY (or OPENAI_API_KEY) is required for video generation")

        create_body = {
            "prompt": prompt,
            "model": self.video_model,
            "size": self.video_size,
            "seconds": self.video_seconds,
        }
        headers = {
            "Content-Type": "application/json",
            "api-key": self.video_api_key,
        }

        create_resp = requests.post(self.video_endpoint, headers=headers, json=create_body, timeout=120)
        if create_resp.status_code >= 400:
            raise RuntimeError(f"video_create_api_error:{create_resp.status_code}:{create_resp.text}")

        task_id = (create_resp.json() or {}).get("id")
        if not task_id:
            raise RuntimeError("video create response missing id")

        started = time.time()
        status_data = {}
        while True:
            status_resp = requests.get(f"{self.video_endpoint}/{task_id}", headers={"api-key": self.video_api_key}, timeout=60)
            status_resp.raise_for_status()
            status_data = status_resp.json() or {}

            status = str(status_data.get("status", "")).lower()
            if status in ("completed", "succeeded"):
                break
            if status == "failed":
                raise RuntimeError(f"video generation failed: {status_data.get('error')}")

            if time.time() - started > self.video_timeout:
                raise TimeoutError(f"timed out waiting for video task {task_id}")

            time.sleep(self.video_poll_interval)

        video_resp = requests.get(f"{self.video_endpoint}/{task_id}/content", headers={"api-key": self.video_api_key}, timeout=180)
        video_resp.raise_for_status()

        video_b64 = base64.b64encode(video_resp.content).decode("utf-8")

        return {
            "mime_type": "video/mp4",
            "data_url": f"data:video/mp4;base64,{video_b64}",
            "task_id": task_id,
            "status": status_data.get("status", "completed"),
            "model": self.video_model,
            "size": self.video_size,
            "seconds": self.video_seconds,
        }
