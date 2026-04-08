# YARA M365 Copilot Integration Script
# Usage: .\Invoke-YaraEvaluation.ps1 -Urls @("url1","url2") -OutputPath "results"

param(
    [Parameter(Mandatory=$true)]
    [string[]]$Urls,
    
    [Parameter(Mandatory=$false)]
    [string]$OutputPath = "evaluation-$(Get-Date -Format 'yyyy-MM-dd-HHmm')",
    
    [Parameter(Mandatory=$false)]
    [switch]$JsonOnly,
    
    [Parameter(Mandatory=$false)]
    [switch]$SummaryOnly
)

# Create temporary URL file
$tempFile = New-TemporaryFile
$Urls | Out-File -FilePath $tempFile.FullName -Encoding UTF8

try {
    # Run YARA evaluation
    $yaraArgs = @(
        "-m", "retrievability.cli", "express", 
        $tempFile.FullName,
        "--out", $OutputPath
    )
    
    if ($SummaryOnly) {
        $yaraArgs += "--quiet"
    }
    
    $result = & python @yaraArgs
    
    if ($JsonOnly) {
        # Return just the JSON scores for programmatic use
        Get-Content "$OutputPath/report_scores.json" | ConvertFrom-Json
    } else {
        # Return full results
        Write-Host $result
        Write-Host "`n📊 Raw scores: $OutputPath/report_scores.json"
        Write-Host "📄 Full report: $OutputPath/report.md"
        Write-Host "🔍 HTML snapshots: $OutputPath/*.html"
    }
    
} finally {
    Remove-Item $tempFile.FullName -Force -ErrorAction SilentlyContinue
}