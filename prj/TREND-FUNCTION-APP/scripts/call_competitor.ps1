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
    input_keyword = $InputKeyword
    max_results = 10
    include_youtube = $true
    country = "KR"
} | ConvertTo-Json -Depth 6

Invoke-RestMethod -Method POST -Uri "$BaseUrl/api/trends/competitor-keyword" -Headers $headers -Body $body
