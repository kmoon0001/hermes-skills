param(
  [Parameter(Mandatory = $true)]
  [string]$Path
)

$ErrorActionPreference = "Stop"

$resolved = Resolve-Path -LiteralPath $Path
$files = Get-ChildItem -LiteralPath $resolved -Recurse -File -Include *.yml,*.yaml |
  Where-Object { $_.FullName -notmatch "\\node_modules\\" }

$results = foreach ($file in $files) {
  $text = Get-Content -LiteralPath $file.FullName -Raw
  $hasSearch = $text -match "kind:\s*SearchAndSummarizeContent"
  $hasEnd = $text -match "kind:\s*EndDialog"
  $hasQuestion = $text -match "kind:\s*Question"
  $hasSendAfterSearch = $text -match "(?s)kind:\s*SearchAndSummarizeContent.*kind:\s*SendActivity.*kind:\s*EndDialog"

  [pscustomobject]@{
    File = $file.FullName
    SearchNoEndDialog = $hasSearch -and -not $hasEnd
    SearchHasQuestion = $hasSearch -and $hasQuestion
    ClearTopicQueueFalse = $text -match "clearTopicQueue:\s*false"
    MissingClearTopicQueueTrue = $hasSearch -and $hasEnd -and -not ($text -match "clearTopicQueue:\s*true")
    ApplyModelKnowledgeFalse = $text -match "applyModelKnowledgeSetting:\s*false"
    SpecificKnowledgeRestriction = $text -match "SearchSpecificFiles|SearchSpecificKnowledgeSources|fileSearchDataSource|knowledgeSources:\s*kind:\s*SearchAllKnowledgeSources"
    LatencyMessageText = $text -match "(?m)^\s*latencyMessage:\s*\S"
    JsonProseConflict = ($text -match "NOT JSON") -and ($text -match "Return exactly one valid JSON")
    BroadMessageTrigger = $text -match "kind:\s*OnActivity(?s).*type:\s*Message"
    SendActivityAfterSearch = $hasSendAfterSearch
  }
}

$issues = $results | Where-Object {
  $_.SearchNoEndDialog -or
  $_.SearchHasQuestion -or
  $_.ClearTopicQueueFalse -or
  $_.MissingClearTopicQueueTrue -or
  $_.ApplyModelKnowledgeFalse -or
  $_.SpecificKnowledgeRestriction -or
  $_.LatencyMessageText -or
  $_.JsonProseConflict -or
  $_.BroadMessageTrigger -or
  $_.SendActivityAfterSearch
}

if (-not $issues) {
  Write-Output "No structural Copilot topic issues detected."
  exit 0
}

$issues | Format-Table -AutoSize
exit 1
