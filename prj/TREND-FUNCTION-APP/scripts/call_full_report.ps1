param(
    [string]$BaseUrl = "http://localhost:7071",
    [string]$FunctionKey = "",
    [string]$InputKeyword = "고유카 카드할인"
)

$headers = @{
    "Content-Type" = "application/json"
}
if ($FunctionKey) {
    $headers["x-functions-key"] = $FunctionKey
}

$body = @{
    schema_version = "v1"
    input_keyword = $InputKeyword
    lookback_days = 90
    country = "KR"
    language = "ko"
    max_results = 15
    include_youtube = $true
} | ConvertTo-Json -Depth 6

Invoke-RestMethod -Method POST -Uri "$BaseUrl/api/trends/full-report" -Headers $headers -Body $body
