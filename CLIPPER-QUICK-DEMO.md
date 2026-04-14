# Clipper Quick Demo Commands

## **Instant Demo (30 seconds)**
```powershell
# Single command demo - works immediately, no setup
python main.py express --urls https://learn.microsoft.com/en-us/azure/azure-functions/functions-overview --out quick-demo --quiet
echo "✅ Clipper Demo Complete! Check quick-demo/ for results"
```

## **Comprehensive Demo (5 minutes)**
```powershell
# Full demo with multiple sites
python main.py express clipper-demo-urls.txt --out clipper-comprehensive --name standards-showcase

# View results
Get-Content clipper-comprehensive/standards-showcase.md
```

## **Interactive Demo (10 minutes)**
```powershell
# Guided walkthrough with explanations
python run_clipper_demo.py
```

## **Component Analysis Demo**
```powershell
# Run evaluation and analyze components
python main.py express clipper-demo-urls.txt --out component-analysis --name detailed

# Show component scores (requires jq: winget install jqlang.jq)
jq '.[] | {url, final_score: .parseability_score, components: .component_scores}' component-analysis/detailed_scores.json

# Show standards authority mapping
jq '.[0].standards_authority' component-analysis/detailed_scores.json
```

## **Enterprise Audit Trail Demo**
```powershell
# Generate audit documentation
python main.py express clipper-demo-urls.txt --out enterprise-demo --name audit-trail

# Examine audit trails (requires jq: winget install jqlang.jq)
jq '.[0].audit_trail' enterprise-demo/audit-trail_scores.json

# Show evaluation methodology  
jq '.[0].evaluation_methodology' enterprise-demo/audit-trail_scores.json
```

## **Quality Gate Simulation**
```powershell
# Simulate CI/CD quality gate
python main.py express clipper-demo-urls.txt --out quality-gate --name gate-test --quiet

# Quality gate logic
python -c "
import json
with open('quality-gate/gate-test_scores.json') as f:
    results = json.load(f)
passed = sum(1 for r in results if r['parseability_score'] >= 70)
total = len(results)
print(f'Quality Gate: {passed}/{total} URLs passed (≥70 points)')
if passed == total:
    print('✅ ALL URLS READY FOR AGENT CONSUMPTION')
else:
    print('⚠️ Some URLs need improvement - check audit trails')
"
```

## **Standards Compliance Check**  
```powershell
# Check WCAG accessibility compliance
python main.py express clipper-demo-urls.txt --out wcag-check --name accessibility

# Filter accessible content (requires jq: winget install jqlang.jq)
jq '.[] | select(.component_scores.wcag_accessibility >= 70) | {url, wcag_score: .component_scores.wcag_accessibility}' wcag-check/accessibility_scores.json
```

---

## **What Each Demo Demonstrates**

### **1. Instant Demo (30 seconds)**
**What it demonstrates:**
- Zero-setup functionality with a single URL
- Uses Microsoft Learn as a high-quality test case
- Shows complete pipeline: crawl → parse → score → report

**Why it's important:**
- **First impression**: Proves Clipper works immediately without configuration
- **Trust building**: Uses recognizable, authoritative content (Microsoft Learn)
- **Friction reduction**: 30-second time commitment removes barriers to trial

### **2. Comprehensive Demo (5 minutes)**  
**What it demonstrates:**
- Batch processing from URL file (`clipper-demo-urls.txt`)
- Named result sets for organization
- Markdown report generation for human consumption

**Why it's important:**
- **Scalability proof**: Shows Clipper handles multiple URLs efficiently
- **Real-world workflow**: Demonstrates how teams would actually use it
- **Output formats**: Shows both JSON (machine) and Markdown (human) outputs

### **3. Interactive Demo (10 minutes)**
**What it demonstrates:**
- Guided walkthrough with explanations (`run_clipper_demo.py`)
- Educational approach to understanding evaluation components

**Why it's important:**
- **Learning tool**: Helps users understand WHY scores are calculated
- **Trust building**: Transparency in evaluation methodology
- **Adoption enabler**: Reduces learning curve for new users

### **4. Component Analysis Demo**
**What it demonstrates:**
- JSON manipulation to extract component-level insights
- Standards authority mapping (WHO sets each standard)
- Deep dive into the 5-component scoring system

**Why it's important:**
- **Technical credibility**: Shows rigorous, decomposable evaluation
- **Debugging capability**: Users can identify exactly why content scored poorly
- **Standards transparency**: Reveals authoritative sources (W3C, WCAG, Schema.org, etc.)

### **5. Enterprise Audit Trail Demo**
**What it demonstrates:**  
- Complete audit trail generation for compliance
- Evaluation methodology documentation
- Reproducible, traceable results

**Why it's important:**
- **Enterprise adoption**: Meets corporate audit/compliance requirements
- **Regulatory compliance**: Supports accessibility and standards documentation
- **Accountability**: Every score can be traced back to specific standards violations

### **6. Quality Gate Simulation**
**What it demonstrates:**
- CI/CD integration with pass/fail logic (≥70 points threshold)
- Automated quality gating for content publication
- Practical DevOps workflow integration

**Why it's important:**
- **Business value**: Prevents poor content from reaching users/agents
- **Automation**: Fits into existing DevOps/CI-CD pipelines
- **Cost savings**: Catches issues early in the publication process

### **7. Standards Compliance Check**
**What it demonstrates:**
- Accessibility-focused filtering (WCAG compliance)
- Component-specific analysis capabilities
- Regulatory compliance validation

**Why it's important:**
- **Legal compliance**: Supports ADA/accessibility requirements
- **Inclusive design**: Ensures content works for all users
- **Risk mitigation**: Identifies accessibility violations before publication

---

## **Strategic Demo Architecture**

### **Progressive Complexity:**
1. **30 seconds** → Quick win, builds confidence
2. **5 minutes** → Real functionality, shows scale  
3. **10 minutes** → Deep understanding, builds expertise

### **Multiple Use Cases:**
- **Developers**: Component analysis, quality gates
- **Compliance teams**: Audit trails, standards checks
- **Content creators**: Accessibility validation, quality improvement

### **Evidence-Based Claims:**
- **No API dependencies** → Immediate usability proof
- **Standards authority** → Credibility through recognized organizations  
- **Enterprise features** → Corporate adoption readiness

---

## **Demo URL Categories**

### **High-Scoring (Expected 80+)**
- Microsoft Learn documentation
- W3C standards documentation  
- Schema.org reference materials

### **Medium-Scoring (Expected 60-80)**  
- Developer platform documentation
- Technical reference sites
- API documentation

### **Mixed Results (Variable)**
- General content sites
- Legacy documentation platforms
- Community-contributed content

---

## **Key Demo Points**

### **🚫 No API Dependencies**
- Works immediately without any setup
- No rate limits or external service dependencies
- Completely offline capable

### **🏛️ Standards Authority** 
- WCAG 2.1 (W3C + Deque Systems) - 25%
- HTML5 Semantic Elements (W3C) - 25%
- Schema.org (Google/Microsoft/Yahoo) - 20%  
- HTTP RFC 7231 (IETF) - 15%
- Agent-focused content analysis - 15%

### **📊 Enterprise Features**
- Complete audit trail generation
- Standards authority documentation
- Reproducible evaluation methodology
- Component-level scoring breakdown

### **🎯 Practical Value**
- Quality gate automation for CI/CD
- Pre-publication content validation
- Agent training data curation
- Compliance documentation generation

---

**Start with any command above - Clipper works immediately!**