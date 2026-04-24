param(
  [string]$Root = 'evaluation/phase5-results/corpus-002'
)

$pattern = '(sk_test|sk_live|pk_live|pk_test|rk_live|rk_test)_[A-Za-z0-9]{6,}'
$targets = Get-ChildItem -Path $Root -Recurse -File -Include *.html,*.txt,*.json,*.md
$totalReplaced = 0
$filesChanged = 0

foreach ($f in $targets) {
  $content = Get-Content -Raw -LiteralPath $f.FullName -Encoding UTF8
  if ($null -eq $content) { continue }
  $m = [regex]::Matches($content, $pattern)
  if ($m.Count -gt 0) {
    $new = [regex]::Replace($content, $pattern, '$1_REDACTED')
    Set-Content -LiteralPath $f.FullName -Value $new -Encoding UTF8 -NoNewline
    $filesChanged++
    $totalReplaced += $m.Count
    $rel = $f.FullName.Substring($PWD.Path.Length + 1)
    Write-Host ("[{0}] {1} -> {2} replacements" -f $filesChanged, $rel, $m.Count)
  }
}

Write-Host ""
Write-Host ("SUMMARY: {0} files changed, {1} total replacements" -f $filesChanged, $totalReplaced)
