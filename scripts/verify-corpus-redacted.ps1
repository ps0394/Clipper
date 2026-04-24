param(
  [string]$Root = 'evaluation/phase5-results/corpus-002'
)

# Match secret-looking tokens that are NOT already redacted
$pattern = '(sk_test|sk_live|pk_live|pk_test|rk_live|rk_test)_(?!REDACTED)[A-Za-z0-9]{6,}'
$hits = @()

Get-ChildItem -Path $Root -Recurse -File -Include *.html,*.txt,*.json,*.md | ForEach-Object {
  $c = Get-Content -Raw -LiteralPath $_.FullName -Encoding UTF8
  if ($null -eq $c) { return }
  $m = [regex]::Matches($c, $pattern)
  if ($m.Count -gt 0) {
    $rel = $_.FullName.Substring($PWD.Path.Length + 1)
    $hits += [PSCustomObject]@{ File = $rel; Count = $m.Count; Sample = $m[0].Value }
  }
}

if ($hits.Count -eq 0) {
  Write-Host "CLEAN: zero unredacted secret matches in $Root" -ForegroundColor Green
  exit 0
} else {
  Write-Host "DIRTY: $($hits.Count) files still contain secrets" -ForegroundColor Red
  $hits | Format-Table -AutoSize
  exit 1
}
