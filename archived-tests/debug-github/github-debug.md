# Retrievability Evaluation Report

Generated: 2026-04-08 16:18:25
Total Pages Evaluated: 1

## Executive Summary

- **Average Parseability Score**: 71.0/100
- **Clean Pages**: 0 (0.0%)
- **Structure Issues**: 0 (0.0%)
- **Extraction Issues**: 1 (100.0%)

## Failure Mode Analysis

### Distribution

| Failure Mode | Count | Percentage | Description |
|--------------|-------|------------|-------------|
| clean | 0 | 0.0% | Ready for retrieval systems |
| structure-missing | 0 | 0.0% | Lacks semantic HTML structure |
| extraction-noisy | 1 | 100.0% | Has structure but content extraction issues |

## Individual Page Results

### ⚠️ Page 1

**Overall Score**: 71.0/100
**Failure Mode**: `extraction-noisy`

**Fix Owner:**

- **Frontend Developer** - Improve content/chrome separation and reduce boilerplate dominance

**Component Scores:**

- Semantic Structure: 60.0/100
- Heading Hierarchy: 100.0/100
- Content Density: 79.4/100
- Rich Content: 0.0/100
- Boilerplate Resistance: 80.6/100

---

## Recommendations

**For extraction-noisy pages**: Reduce navigation/sidebar dominance by moving primary content higher in DOM order and using clearer content boundaries.
