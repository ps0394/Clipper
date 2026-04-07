#!/usr/bin/env pwsh
<#
.SYNOPSIS
    GitHub Agent for URL Evaluation (PowerShell version)
    
.DESCRIPTION
    Simple agent interface that triggers URL evaluation workflows and returns results.
    
.PARAMETER Urls
    URLs to evaluate (space-separated)
    
.PARAMETER File
    File containing URLs (one per line)
    
.PARAMETER Name  
    Name for this evaluation run
    
.EXAMPLE
    .\url-agent.ps1 -Urls "https://docs.microsoft.com/azure" "https://github.com/docs"
    .\url-agent.ps1 -File "my-urls.txt" -Name "my-test" 
#>

param(
    [string[]]$Urls = @(),
    [string]$File = "",
    [string]$Name = "agent-eval",
    [string]$Repo = "ps0394/Retrieval"
)

function Start-URLEvaluation {
    param($UrlList, $EvalName)
    
    Write-Host "🤖 Agent evaluating $($UrlList.Count) URLs..." -ForegroundColor Cyan
    
    # Format URLs for workflow input
    $urlsText = $UrlList -join "`n"
    
    # Trigger workflow via GitHub CLI
    Write-Host "🚀 Triggering evaluation workflow..." -ForegroundColor Yellow
    
    try {
        & gh workflow run "quick-evaluate.yml" --repo $Repo -f "urls=$urlsText" -f "output_name=$EvalName"
        Write-Host "✅ Workflow triggered successfully" -ForegroundColor Green
        
        # Wait for completion 
        Write-Host "⏳ Waiting for evaluation to complete..." -ForegroundColor Yellow
        
        $maxWait = 300  # 5 minutes
        $startTime = Get-Date
        
        do {
            Start-Sleep -Seconds 10
            
            $runs = & gh run list --repo $Repo --workflow "quick-evaluate.yml" --limit 1 --json "status,conclusion,number,url" | ConvertFrom-Json
            
            if ($runs -and $runs[0].status -eq "completed") {
                if ($runs[0].conclusion -eq "success") {
                    Write-Host "✅ Evaluation completed successfully!" -ForegroundColor Green
                    
                    # Get results
                    Write-Host "📥 Downloading results..." -ForegroundColor Cyan
                    
                    # Try to get workflow summary via API
                    $runUrl = "https://github.com/$Repo/actions/runs/$($runs[0].number)"
                    Write-Host "`n$('='*50)" -ForegroundColor Magenta
                    Write-Host "📊 EVALUATION COMPLETED" -ForegroundColor Magenta  
                    Write-Host "$('='*50)" -ForegroundColor Magenta
                    Write-Host "🔗 View results: $runUrl"
                    Write-Host "💡 Check the 'Summary' tab for detailed results"
                    
                    return $true
                } else {
                    Write-Host "❌ Evaluation failed: $($runs[0].conclusion)" -ForegroundColor Red
                    Write-Host "🔗 Check details: $($runs[0].url)"
                    return $false
                }
            }
            
            $elapsed = (Get-Date) - $startTime
            Write-Host "⏳ Still running... ($([int]$elapsed.TotalSeconds)s elapsed)" -ForegroundColor Yellow
            
        } while ($elapsed.TotalSeconds -lt $maxWait)
        
        Write-Host "⏰ Timeout waiting for results" -ForegroundColor Red
        return $false
        
    } catch {
        Write-Host "❌ Failed to trigger workflow: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Main execution
$allUrls = @()

# Collect URLs from file
if ($File) {
    if (Test-Path $File) {
        $fileUrls = Get-Content $File | Where-Object { $_.Trim() -ne "" }
        $allUrls += $fileUrls
        Write-Host "📁 Loaded $($fileUrls.Count) URLs from $File" -ForegroundColor Green
    } else {
        Write-Host "❌ File not found: $File" -ForegroundColor Red
        exit 1
    }
}

# Add URLs from parameters
$allUrls += $Urls

if ($allUrls.Count -eq 0) {
    Write-Host "❌ No URLs provided!" -ForegroundColor Red
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\url-agent.ps1 -Urls 'https://example.com' 'https://test.com'" -ForegroundColor White
    Write-Host "  .\url-agent.ps1 -File 'urls.txt'" -ForegroundColor White
    exit 1
}

Write-Host "🎯 URLs to evaluate:" -ForegroundColor Cyan
$allUrls | ForEach-Object { Write-Host "   • $_" -ForegroundColor White }

# Check if GitHub CLI is installed
try {
    & gh --version | Out-Null
} catch {
    Write-Host "❌ GitHub CLI not found! Please install it: https://cli.github.com/" -ForegroundColor Red
    exit 1
}

# Start evaluation
$success = Start-URLEvaluation -UrlList $allUrls -EvalName $Name

if ($success) {
    Write-Host "`n🎉 Agent evaluation completed successfully!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n❌ Agent evaluation failed" -ForegroundColor Red  
    exit 1
}