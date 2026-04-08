# 5-Minute Documentation Quality Demo Script

**Audience**: Documentation teams  
**Goal**: Show how retrievability evaluation helps assess content for AI/search systems  
**Duration**: 5 minutes  
**Demo Type**: **LIVE EXECUTION** with real-time CLI commands
**Files needed**: `demo-urls.txt`, live internet connection + backup results

---

## 🚨 LIVE DEMO PREPARATION CHECKLIST

**CRITICAL**: Test this setup 10 minutes before your demo!

### Pre-Demo Setup (Required)
```bash
# 1. Verify CLI works
python -m retrievability.cli --help

# 2. Test with 1 URL (should complete in ~15 seconds)
echo "https://learn.microsoft.com/en-us/azure/storage/common/storage-introduction" > test.txt
python -m retrievability.cli crawl test.txt --out test/
python -m retrievability.cli parse test/ --out test/parse.json

# 3. Clean up test files
rm -rf test/ test.txt

# 4. Ensure backup results exist
ls demo-results-expanded/  # Should show crawl_results.json, scores.json
ls enhanced-demo-backup.txt  # Phase 1 actionable examples

# 5. Have fallback summary ready
python -c "
import json
with open('demo-results-expanded/crawl_results.json', 'r') as f: crawl = json.load(f)
with open('demo-results-expanded/scores.json', 'r') as f: scores = json.load(f)
results = [(s['parseability_score'], s['failure_mode'], c['url'].split('/')[2]) 
           for c, s in zip(crawl, scores)]
results.sort(reverse=True)
for score, mode, domain in results:
    print(f'{score:.1f} | {mode:15} | {domain}')
" > backup-results.txt
```

### Risk Mitigation
- **Internet dependency**: Have `demo-results-expanded/` pre-generated as backup
- **Timing risk**: Budget 2 minutes for live execution, not 90 seconds  
- **Command failure**: Know how to quickly switch to backup results
- **Audience engagement**: Prepare talking points for command execution time

---

## Pre-Demo Setup (30 seconds)

**SAY**: *"I'm going to show you a tool that evaluates documentation quality for AI systems and gives you actionable fixes with code examples. We'll test 9 real websites and get priority-ranked improvements."*

**SHOW**: Display the demo URLs file
```bash
# Show the test URLs
cat demo-urls.txt
```

**KEY POINT**: "We're testing Microsoft, AWS, Google, Wikipedia, GitHub, and Stack Overflow - sites your teams probably reference daily. But here's the kicker: we'll get specific HTML fixes with before/after code examples."

---

## Live Evaluation (2 minutes)

### ⚡ Express Mode Demo (90 seconds)
**SAY**: *"Let me show you our express mode - complete evaluation with actionable reports in one command."*

```bash
python -m retrievability.cli express demo-urls.txt --out demo-live-results/
```

**💡 Windows PowerShell Note**: If you see Unicode encoding errors, use:
```bash
# Alternative for Windows PowerShell
$env:PYTHONIOENCODING="utf-8"
python -m retrievability.cli express demo-urls.txt --out demo-live-results/
# OR run step-by-step if needed
```

**TALK WHILE RUNNING** (express mode does crawl → parse → score → report automatically):
- "This runs our complete pipeline: crawl, parse, score, and generate actionable reports"
- "We're analyzing semantic structure, heading hierarchy, content density, and boilerplate resistance"
- "The output includes priority-ranked fixes with actual HTML code examples"
- "Notice it's not just scores - it's implementable solutions"

**ALTERNATIVE**: Step-by-step if you want to show the pipeline:
```bash
python -m retrievability.cli crawl demo-urls.txt --out demo-live-results/
python -m retrievability.cli parse demo-live-results/ --out demo-live-results/parse.json
python -m retrievability.cli score demo-live-results/parse.json --out demo-live-results/scores.json
python -m retrievability.cli report demo-live-results/scores.json --md demo-live-results/report.md
```

---

## Results Analysis (2.5 minutes)

### Show the Rankings
**LIVE RESULTS** (if everything worked):
```bash
python -c "
import json
with open('demo-live-results/crawl_results.json', 'r') as f: crawl = json.load(f)
with open('demo-live-results/scores.json', 'r') as f: scores = json.load(f)
results = [(s['parseability_score'], s['failure_mode'], c['url'].split('/')[2]) 
           for c, s in zip(crawl, scores)]
results.sort(reverse=True)
for score, mode, domain in results:
    print(f'{score:.1f} | {mode:15} | {domain}')
"
```

**BACKUP RESULTS** (if live demo had issues):
```bash
cat enhanced-demo-backup.txt  # Shows Phase 1 features
# OR original backup:
cat backup-results.txt  # Simple ranking
# OR from expanded results:
python -c "
import json
with open('demo-results-expanded/crawl_results.json', 'r') as f: crawl = json.load(f)
with open('demo-results-expanded/scores.json', 'r') as f: scores = json.load(f)
# ... same script as above
"
```

**TRANSITION**: *"Here are the results - and I guarantee this will shock you:"*

### The Shocking Results (60 seconds)

**SAY**: *"Here's what we found - and the actionable insights will transform how you think about documentation:"*

**TOP PERFORMERS (85-88 points)**:
- 🏆 **Wikipedia**: "Excellent semantic structure - and we'll show you exactly how to copy their approach"
- ✅ **Microsoft Learn**: "Enterprise documentation standard with clear improvement roadmap"

**MIDDLE TIER (75-80 points)**:  
- ⚠️ **Google Developer Docs**: "Good content, but our report shows 3 specific fixes worth +15 points"

**POOR PERFORMERS (40-65 points)**:
- ❌ **AWS Docs**: "Missing semantic HTML - but 2 code changes get them to 80+"  
- ❌ **Google Cloud**: "Major structure gaps - priority fixes identified"
- ❌ **GitHub Docs**: "Boilerplate contamination - we show exact HTML patterns to fix it"
- ❌ **Stack Overflow**: "Heavy navigation overwhelming content - actionable solutions provided"

### 🎯 Actionable Report Showcase (90 seconds)

**SHOW THE ACTIONABLE MAGIC**:
```bash
cat demo-live-results/report.md  # Show actual actionable report
# OR use backup: cat enhanced-report.md
```

**HIGHLIGHT KEY FEATURES** (point to actual report sections):

**1. Priority-Ranked Fixes**:
*"Look at this table - it tells teams exactly what to fix first:"*

```
| Fix | Impact | Effort | Score Gain | Priority |
| Add `<main>` element | High | Low | +15 pts | 🔥 Critical |
| Fix heading hierarchy | High | Medium | +12 pts | 🔥 Critical |
```

**2. Copy-Paste Code Examples**:
*"No more abstract advice - here's exact HTML to fix every issue:"*

```html
<!-- Before (problematic) -->
<div class="content">
  <h1>Page Title</h1>
  
<!-- After (semantic) -->
<main>
  <article>
    <h1>Page Title</h1>
```

**3. Content Beats Brand Names**:
*"Wikipedia (88 points) outperforms AWS (63) and Google Cloud (51). Why? Better semantic structure, not bigger engineering teams."*

---

## Takeaways & Next Steps (60 seconds)

### What Documentation Teams Get Now
**SAY**: *"This isn't just analysis - it's a complete improvement roadmap:"*

**🎯 Priority-Driven Action Plan**:
- **Impact scoring**: Which fixes give biggest score improvements
- **Effort estimates**: Low/Medium/High implementation difficulty  
- **Score predictions**: Expected point gains (+15 pts, +12 pts, etc.)
- **Visual priorities**: 🔥 Critical, ⚠️ Important, 📋 Planned

**💻 Copy-Paste Solutions**:
- **Before/after HTML**: See exactly what to change
- **Framework-agnostic**: Works with React, Vue, static sites, CMSs
- **Semantic patterns**: `<main>`, `<article>`, heading hierarchy
- **Content organization**: Reduce boilerplate contamination

### Integration Options That Actually Work
**OPTION 1 - Express Audit**: 
```bash
python -m retrievability.cli express your-urls.txt --out results/
cat results/report.md  # Get actionable fixes immediately
```

**OPTION 2 - GitHub Quality Gates**: 
```yaml
- uses: ps0394/Retrieval/.github/actions/docs-eval@main
  with:
    urls-file: 'docs/urls.txt'
    min-score: '75'
# Blocks deployment if quality drops
```

**OPTION 3 - Pre-Publication Checks**:
```bash
# Before publishing new docs
echo "https://staging.example.com/new-guide" > staging.txt
python -m retrievability.cli express staging.txt --out staging-check/
cat staging-check/report.md  # Get specific fixes before going live
```

### The Bottom Line
**SAY**: *"In 5 minutes, we've shown you that content structure beats everything else. Wikipedia, with no 'modern' docs infrastructure, outperformed AWS and Google because they focus on semantic HTML and content organization. Your teams can do the same - and now you have the exact roadmap to get there."*

**FINAL MESSAGE**: *"This tool doesn't just tell you what's broken - it shows you exactly how to fix it, prioritizes your work, and gives you copy-paste solutions. Documentation quality is no longer a mystery."*

---

## 🛡️ LIVE DEMO BACKUP PLANS

### If Internet Connection Fails
**IMMEDIATE SWITCH**: *"Let me show you results from a recent evaluation run..."*
```bash
cat backup-results.txt
```
**SAY**: *"Same evaluation, same shocking results - Wikipedia beat AWS and Google."*

### If Commands Take Too Long  
**AFTER 45 SECONDS**: *"This is taking longer than usual - let me show you what we typically see..."*
**CTRL+C** and switch to backup results
**SAY**: *"In production, this runs in under 60 seconds, but networks vary."*

### If CLI Errors Occur
**UNICODE/ENCODING ISSUES** (Windows PowerShell): 
```bash
$env:PYTHONIOENCODING="utf-8"  # Set encoding
chcp 65001  # Change console to UTF-8
```
**DEPENDENCY ISSUES**: 
```bash
pip install -r requirements.txt  # Quick fix attempt
```
**PARSING FAILURES**: Switch to pre-generated results immediately
**FILE PERMISSION ERRORS**: Use `demo-results-expanded/` instead of creating new directory

### If Demo Runs Over Time
**PRIORITY ORDER**:
1. Show results ranking (30 seconds) 
2. Wikipedia beats Big Tech insight (30 seconds)
3. Structure matters most message (30 seconds)
4. **Skip**: Detailed breakdown, integration options

### Recovery Phrases
- *"Technology demos - you know how it is! But the insights remain the same..."*
- *"The network is slow today, but I have recent results that show the same patterns..."*
- *"This is why we always have backups - let me show you what this typically looks like..."*

---

## Demo Success Metrics
- ✅ Audience understands 5 scoring dimensions
- ✅ Shock at Wikipedia beating AWS/Google  
- ✅ Recognition that content structure beats brand name
- ✅ Interest in trying the tool on their own documentation
- ✅ Questions about integration options

---

## Why Live Demo Works Best

**ADVANTAGES**:
- **Credibility**: Audience sees real analysis happening, not canned results
- **Engagement**: Live commands keep audience attention during execution
- **Flexibility**: Can adjust URLs or answer questions about specific sites
- **Authenticity**: Shows tool is production-ready and fast enough for daily use

**TIMING VALIDATION**:
- ✅ Crawl: ~30 seconds execution + 15 seconds explanation  
- ✅ Parse/Score: ~45 seconds execution + 30 seconds explanation
- ✅ Results: Pre-generated backup takes 10 seconds to display
- ✅ Total: 2.5 minutes with buffer for smooth delivery

**RISK MITIGATION**: Every potential failure has a smooth backup transition that preserves the demo narrative and impact.