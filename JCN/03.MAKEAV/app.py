#!/usr/bin/env python3
"""Prompt-to-video module for Azure Foundry app function usage."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()


@dataclass
class SoraConfig:
    endpoint: str
    api_key: str
    model: str
    seconds: str
    size: str
    poll_interval_seconds: int = 3
    timeout_seconds: int = 600


ALLOWED_SECONDS = {"4", "8", "12"}


def load_config() -> SoraConfig:
    endpoint = os.getenv("AZURE_SORA_VIDEO_URL", "").strip().rstrip("/")
    if not endpoint:
        endpoint = "https://testuser27-4790-resource.cognitiveservices.azure.com/openai/v1/videos"

    api_key = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("AZURE_OPENAI_API_KEY is required")

    seconds = os.getenv("VIDEO_SECONDS", "8").strip()
    if seconds not in ALLOWED_SECONDS:
        seconds = "8"

    return SoraConfig(
        endpoint=endpoint,
        api_key=api_key,
        model=os.getenv("AZURE_SORA_DEPLOYMENT", "sora-2").strip() or "sora-2",
        seconds=seconds,
        size=os.getenv("VIDEO_SIZE", "1280x720").strip() or "1280x720",
    )


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "api-key": api_key,
    }


def create_video(prompt: str, config: SoraConfig) -> str:
    payload = {
        "prompt": prompt,
        "model": config.model,
        "size": config.size,
        "seconds": config.seconds,
    }

    with httpx.Client(timeout=60) as client:
        resp = client.post(config.endpoint, headers=_headers(config.api_key), json=payload)

    if resp.status_code not in (200, 202):
        raise RuntimeError(f"Video create failed: {resp.status_code} {resp.text}")

    task_id = resp.json().get("id")
    if not task_id:
        raise RuntimeError("Video create response missing id")

    return task_id


def wait_until_complete(task_id: str, config: SoraConfig) -> dict[str, Any]:
    start = time.time()

    with httpx.Client(timeout=30) as client:
        while True:
            resp = client.get(f"{config.endpoint}/{task_id}", headers=_headers(config.api_key))
            if resp.status_code not in (200, 202):
                raise RuntimeError(f"Status check failed: {resp.status_code} {resp.text}")

            data = resp.json()
            status = data.get("status", "unknown")

            if status in ("completed", "succeeded"):
                return data
            if status == "failed":
                raise RuntimeError(f"Video generation failed: {data.get('error')}")

            if (time.time() - start) > config.timeout_seconds:
                raise TimeoutError(f"Timed out after {config.timeout_seconds}s waiting for video")

            time.sleep(config.poll_interval_seconds)


def download_video(task_id: str, output_file: Path, config: SoraConfig) -> Path:
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with httpx.Client(timeout=180) as client:
        resp = client.get(f"{config.endpoint}/{task_id}/content", headers={"api-key": config.api_key})

    if resp.status_code != 200:
        raise RuntimeError(f"Video download failed: {resp.status_code} {resp.text}")

    output_file.write_bytes(resp.content)
    return output_file


def generate_video_file(prompt: str, output_dir: str = "outputs") -> dict[str, Any]:
    """Main module function: prompt input -> mp4 file output."""
    if not prompt or not prompt.strip():
        raise ValueError("prompt is required")

    config = load_config()
    task_id = create_video(prompt.strip(), config)
    result = wait_until_complete(task_id, config)

    created_at = result.get("created_at")
    completed_at = result.get("completed_at")
    elapsed_seconds = None
    if isinstance(created_at, int) and isinstance(completed_at, int) and completed_at >= created_at:
        elapsed_seconds = completed_at - created_at

    file_path = Path(output_dir) / f"{task_id}.mp4"
    download_video(task_id, file_path, config)

    return {
        "task_id": task_id,
        "status": result.get("status", "completed"),
        "elapsed_seconds": elapsed_seconds,
        "video_file": str(file_path),
    }


def app_function(input_data: dict[str, Any]) -> dict[str, Any]:
    """Azure Foundry app function entry point."""
    prompt = str(input_data.get("prompt", "")).strip()
    if not prompt:
        raise ValueError("input_data.prompt is required")

    output_dir = str(input_data.get("output_dir", "outputs")).strip() or "outputs"
    return generate_video_file(prompt=prompt, output_dir=output_dir)


if __name__ == "__main__":
    sample_prompt = os.getenv("PROMPT", "부산은행 여름 신용카드 마케팅 영상")
    print(app_function({"prompt": sample_prompt}))
