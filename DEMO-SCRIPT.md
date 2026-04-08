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

**SAY**: *"I'm going to show you a tool that evaluates how well documentation works with AI systems and search engines. We'll test 9 real websites including major cloud providers."*

**SHOW**: Display the demo URLs file
```bash
# Show the test URLs
cat demo-urls.txt
```

**KEY POINT**: "We're testing Microsoft, AWS, Google, Wikipedia, GitHub, and Stack Overflow - sites your teams probably reference daily."

---

## Live Evaluation (2 minutes)

### Step 1: Crawl (45 seconds)
**SAY**: *"Let's evaluate these 9 sites in real-time. First, we fetch all the pages."*

```bash
python -m retrievability.cli crawl demo-urls.txt --out demo-live-results/
```

**TALK WHILE CRAWLING** (~30 seconds of execution time):
- "We're grabbing HTML from each site - Microsoft, AWS, Google, Wikipedia..."
- "The tool saves snapshots locally so analysis is consistent and repeatable"  
- "Notice we're testing the sites your teams probably reference daily"
- **Watch for**: All 9 URLs should crawl successfully (status 200)

**IF INTERNET ISSUES**: Immediately switch to backup: *"Let me show you results from a recent run..."*

### Step 2: Parse & Score (75 seconds)
**SAY**: *"Now we analyze the HTML and calculate retrievability scores based on 5 dimensions."*

```bash
python -m retrievability.cli parse demo-live-results/ --out demo-live-results/parse.json
python -m retrievability.cli score demo-live-results/parse.json --out demo-live-results/scores.json  
```

**EXPLAIN THE 5 SCORING DIMENSIONS WHILE COMMANDS RUN**:
1. **Semantic Structure** (25%) - "Does it use `<main>`, `<article>` elements?"
2. **Heading Hierarchy** (20%) - "Is the H1→H2→H3 flow logical?" 
3. **Content Density** (25%) - "How much actual content vs. navigation/chrome?"
4. **Rich Content** (10%) - "Are there code blocks, tables, structured data?"
5. **Boilerplate Resistance** (20%) - "Can AI extract content without noise?"

**KEY MESSAGE WHILE PROCESSING**: *"These aren't subjective opinions - these are deterministic signals that predict how well AI systems can work with your content."*

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
cat backup-results.txt  # Pre-generated summary
# OR
python -c "
import json
with open('demo-results-expanded/crawl_results.json', 'r') as f: crawl = json.load(f)
with open('demo-results-expanded/scores.json', 'r') as f: scores = json.load(f)
# ... same script as above
"
```

**TRANSITION**: *"Here are the results - and I guarantee this will shock you:"*

### The Shocking Results (60 seconds)

**SAY**: *"Here's what we found - and it might surprise you:"*

**TOP PERFORMERS (85-88 points)**:
- 🏆 **Wikipedia**: "Excellent content density and semantic structure"
- ✅ **Microsoft Learn**: "Consistent enterprise documentation standards"

**MIDDLE TIER (75-80 points)**:  
- ⚠️ **Google Developer Docs**: "Good content, but extraction challenges"

**POOR PERFORMERS (40-65 points)**:
- ❌ **AWS Docs**: "Missing semantic HTML structure"  
- ❌ **Google Cloud**: "Major structure gaps"
- ❌ **GitHub Docs**: "Boilerplate contamination"
- ❌ **Stack Overflow**: "Heavy navigation, poor content extraction"

### Key Insights for Documentation Teams (90 seconds)

**INSIGHT 1 - Content beats brand**: 
*"Wikipedia outperforms AWS and Google Cloud. It's not about company size - it's about technical approach to content structure."*

**INSIGHT 2 - Structure is everything**:
*"The difference between 88 points and 42 points? Semantic HTML elements and proper heading hierarchy."*

**INSIGHT 3 - Boilerplate kills performance**:
*"Even good content fails if it's drowning in navigation, sidebars, and chrome."*

**SHOW DETAILED BREAKDOWN** (if time permits):
```bash
python -m retrievability.cli report demo-results/scores.json --md demo-results/report.md
# Show specific failure modes and fix recommendations
```

---

## Takeaways & Next Steps (60 seconds)

### What Documentation Teams Should Track
**SAY**: *"Here are the metrics that matter for your content:"*

1. **Semantic Structure Score** - Are you using `<main>` and `<article>` elements?
2. **Content Density Ratio** - How much of your page is actual content vs. chrome?
3. **Heading Hierarchy Health** - Is your H1→H2→H3 flow logical?
4. **Boilerplate Resistance** - Can AI systems extract your content cleanly?

### Quick Integration Options
**OPTION 1 - CLI Audit**: `python -m retrievability.cli express your-urls.txt --out results/`

**OPTION 2 - GitHub Integration**: Add our reusable action to your workflow:
```yaml
- uses: ps0394/Retrieval/.github/actions/docs-eval@main
  with:
    urls-file: 'docs/urls.txt'
    min-score: '75'
```

**OPTION 3 - One-off Agent**: `scripts/url-agent.py --file urls.txt --name "audit"`

### The Bottom Line
**SAY**: *"In 5 minutes, we evaluated 9 major documentation sites and found that content structure beats everything else. Wikipedia, with no engineering budget for 'modern' docs infrastructure, outperformed AWS and Google because they focus on semantic HTML and content density."*

**FINAL MESSAGE**: *"Your documentation teams can compete with Big Tech by focusing on the fundamentals: clean semantic structure, logical headings, and minimal chrome contamination."*

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