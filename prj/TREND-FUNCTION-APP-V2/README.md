# TREND-FUNCTION-APP-V2

This is an isolated Azure Functions app intended for new trigger-based workflows.
It is managed separately from the existing root app.

## Endpoint

- POST `/api/trends/trending-meme-final`

## What It Does

1. Scrapes posts from the recent 50-day window with article body included.
2. Sorts by latest published date and limits to the newest records.
3. Saves raw and summary JSON outputs.
4. Returns summarized trending meme results.

## Local Run

```powershell
cd apps/trend-function-app-v2
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
func start
```

## Trigger Request Example

```json
{
  "max_results": 20,
  "max_total_posts": 300,
  "max_articles_per_source": 100,
  "persist_output": true
}
```

## Output Files

- `data/reports/scraped_posts_50d_latest.json`
- `data/reports/scraped_posts_50d_YYYYMMDD_HHMMSS.json`
- `data/reports/trending_memes_latest.json`
- `data/reports/trending_memes_YYYYMMDD_HHMMSS.json`
