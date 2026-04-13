# Clipper Quick Demo Commands

## **Instant Demo (30 seconds)**
```bash
# Single command demo - works immediately, no setup
python main.py express --urls https://learn.microsoft.com/en-us/azure/azure-functions/functions-overview --out quick-demo --quiet && echo "✅ Clipper Demo Complete! Check quick-demo/ for results"
```

## **Comprehensive Demo (5 minutes)**
```bash
# Full demo with multiple sites
python main.py express clipper-demo-urls.txt --out clipper-comprehensive --name standards-showcase

# View results
cat clipper-comprehensive/standards-showcase.md
```

## **Interactive Demo (10 minutes)**
```bash
# Guided walkthrough with explanations
python run_clipper_demo.py
```

## **Component Analysis Demo**
```bash
# Run evaluation and analyze components
python main.py express clipper-demo-urls.txt --out component-analysis --name detailed

# Show component scores
jq '.[] | {url, final_score: .parseability_score, components: .component_scores}' component-analysis/detailed_scores.json

# Show standards authority mapping
jq '.[0].standards_authority' component-analysis/detailed_scores.json
```

## **Enterprise Audit Trail Demo**
```bash
# Generate audit documentation
python main.py express clipper-demo-urls.txt --out enterprise-demo --name audit-trail

# Examine audit trails
jq '.[0].audit_trail' enterprise-demo/audit-trail_scores.json

# Show evaluation methodology  
jq '.[0].evaluation_methodology' enterprise-demo/audit-trail_scores.json
```

## **Quality Gate Simulation**
```bash
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
```bash
# Check WCAG accessibility compliance
python main.py express clipper-demo-urls.txt --out wcag-check --name accessibility

# Filter accessible content
jq '.[] | select(.component_scores.wcag_accessibility >= 70) | {url, wcag_score: .component_scores.wcag_accessibility}' wcag-check/accessibility_scores.json
```

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