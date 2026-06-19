# 03.MAKEAV

Prompt-to-video module for Azure Foundry app function.

## Input
- `prompt` (string): detailed prompt text

## Output
- mp4 file path (`video_file`)

## Setup
1. Copy `.env.example` to `.env`
2. Fill `AZURE_OPENAI_API_KEY` and `AZURE_SORA_VIDEO_URL`
3. Install packages:

```powershell
pip install -r requirements.txt
```

## Azure Foundry app function entry
- Function: `app_function(input_data)` in `app.py`
- Example input:

```json
{
  "prompt": "부산은행 여름 프로모션 카드 광고 영상"
}
```

- Example output:

```json
{
  "task_id": "video_xxx",
  "status": "completed",
  "elapsed_seconds": 72,
  "video_file": "outputs/video_xxx.mp4"
}
```
