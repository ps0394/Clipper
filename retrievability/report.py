"""Report generation for retrievability evaluation results."""

import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from .schemas import ScoreResult


def generate_report(score_file: str, output_md: str) -> None:
    """Generate human-readable markdown report from score results.
    
    Args:
        score_file: JSON file with score results
        output_md: Markdown file to save report
    """
    score_path = Path(score_file)
    if not score_path.exists():
        raise FileNotFoundError(f"Score file not found: {score_file}")
    
    with open(score_path, 'r', encoding='utf-8') as f:
        score_results_data = json.load(f)
    
    # Generate markdown report content
    report_content = _generate_markdown_report(score_results_data)
    
    # Save markdown report
    output_path = Path(output_md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"Report generated: {output_md}")


def _generate_markdown_report(score_results: List[Dict]) -> str:
    """Generate markdown report content.
    
    Args:
        score_results: List of score result dictionaries
        
    Returns:
        Markdown report content
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Calculate summary statistics
    total_pages = len(score_results)
    clean_pages = sum(1 for result in score_results if result['failure_mode'] == 'clean')
    structure_missing = sum(1 for result in score_results if result['failure_mode'] == 'structure-missing')
    extraction_noisy = sum(1 for result in score_results if result['failure_mode'] == 'extraction-noisy')
    
    avg_score = sum(result['parseability_score'] for result in score_results) / total_pages if total_pages > 0 else 0
    
    # Build report sections
    report_lines = []
    
    # Header
    report_lines.extend([
        "# Retrievability Evaluation Report",
        "",
        f"Generated: {timestamp}",
        f"Total Pages Evaluated: {total_pages}",
        "",
        "## Executive Summary",
        "",
        f"- **Average Parseability Score**: {avg_score:.1f}/100",
        f"- **Clean Pages**: {clean_pages} ({clean_pages/total_pages*100:.1f}%)",
        f"- **Structure Issues**: {structure_missing} ({structure_missing/total_pages*100:.1f}%)",
        f"- **Extraction Issues**: {extraction_noisy} ({extraction_noisy/total_pages*100:.1f}%)",
        ""
    ])
    
    # Failure mode breakdown
    report_lines.extend([
        "## Failure Mode Analysis",
        "",
        "### Distribution",
        "",
        "| Failure Mode | Count | Percentage | Description |",
        "|--------------|-------|------------|-------------|",
        f"| clean | {clean_pages} | {clean_pages/total_pages*100:.1f}% | Ready for retrieval systems |",
        f"| structure-missing | {structure_missing} | {structure_missing/total_pages*100:.1f}% | Lacks semantic HTML structure |",
        f"| extraction-noisy | {extraction_noisy} | {extraction_noisy/total_pages*100:.1f}% | Has structure but content extraction issues |",
        ""
    ])
    
    # Individual page results
    report_lines.extend([
        "## Individual Page Results",
        ""
    ])
    
    # Sort by score (lowest first - most problematic)
    sorted_results = sorted(score_results, key=lambda x: x['parseability_score'])
    
    for i, result in enumerate(sorted_results, 1):
        score = result['parseability_score']
        failure_mode = result['failure_mode']
        # Use correct field names from Clipper format
        component_scores = result.get('component_scores', result.get('subscores', {}))
        audit_trail = result.get('audit_trail', {})
        
        # Extract evidence references from audit trail
        evidence = []
        for component, trail_data in audit_trail.items():
            if isinstance(trail_data, dict) and 'violations' in trail_data:
                evidence.append(f"{component}: {len(trail_data['violations'])} violations found")
            elif isinstance(trail_data, dict) and 'evidence' in trail_data:
                if isinstance(trail_data['evidence'], list):
                    evidence.extend(trail_data['evidence'])
                else:
                    evidence.append(str(trail_data['evidence']))
        
        # Fallback to legacy evidence_references if available
        if not evidence and 'evidence_references' in result and result['evidence_references']:
            evidence = result['evidence_references']
        
        # Determine page identifier (use html_path as proxy for URL)
        page_id = result.get('html_path', f'Page {i}')
        
        # Status emoji
        if failure_mode == 'clean':
            status_emoji = "[PASS]"
        elif failure_mode == 'structure-missing':
            status_emoji = "[FAIL]"
        else:  # extraction-noisy
            status_emoji = "[WARN]"
        
        report_lines.extend([
            f"### {status_emoji} {page_id}",
            "",
            f"**Overall Score**: {score:.1f}/100",
            f"**Failure Mode**: `{failure_mode}`",
            ""
        ])

        # Extracted preview (Phase 1.2): surface what Mozilla Readability pulled
        # out so a low extractability score has a visible cause.
        extractability_audit = audit_trail.get('content_extractability', {})
        extraction_metrics = extractability_audit.get('extraction_metrics', {}) if isinstance(extractability_audit, dict) else {}
        extracted_preview = extraction_metrics.get('extracted_preview')
        extracted_chars = extraction_metrics.get('extracted_chars')
        if extracted_preview is not None:
            extract_score = component_scores.get('content_extractability')
            header = "**Extracted Preview**"
            if extract_score is not None:
                header += f" (extractability {extract_score:.1f}/100"
                if extracted_chars is not None:
                    header += f", {extracted_chars:,} chars extracted"
                header += "):"
            else:
                header += ":"
            report_lines.extend([
                header,
                "",
                "> " + (extracted_preview.replace("\n", " ").strip() or "_(empty extraction)_"),
                "",
            ])

        # What failed?
        issues = _identify_issues(failure_mode, component_scores)
        if issues:
            report_lines.extend([
                "**What Failed:**",
                ""
            ])
            for issue in issues:
                report_lines.append(f"- {issue}")
            report_lines.append("")
        
        # Why did it fail?
        root_causes = _identify_root_causes(failure_mode, component_scores, evidence)
        if root_causes:
            report_lines.extend([
                "**Why It Failed:**",
                ""
            ])
            for cause in root_causes:
                report_lines.append(f"- {cause}")
            report_lines.append("")
        
        # Who owns the fix?
        owner_guidance = _identify_fix_owner(failure_mode, component_scores)
        if owner_guidance:
            report_lines.extend([
                "**Fix Owner:**",
                "",
                f"- {owner_guidance}",
                ""
            ])
        
        # Priority fixes (NEW)
        priority_fixes = _generate_priority_fixes(failure_mode, component_scores, score)
        if priority_fixes:
            report_lines.extend([
                "**Priority Fixes:**",
                "",
                "| Fix | Impact | Effort | Score Gain | Priority |",
                "|-----|--------|--------|------------|----------|",
            ])
            for fix in priority_fixes:
                report_lines.append(f"| {fix['name']} | {fix['impact']} | {fix['effort']} | +{fix['score_gain']} pts | {fix['priority']} |")
            report_lines.append("")
        
        # Code examples (NEW)
        code_examples = _generate_code_examples(failure_mode, component_scores)
        if code_examples:
            report_lines.extend([
                "**How to Fix:**",
                "",
            ])
            for example in code_examples:
                report_lines.extend([
                    f"**{example['title']}:**",
                    "```html",
                    example['code'],
                    "```",
                    ""
                ])
        
        # Component scores
        report_lines.extend([
            "**Component Scores:**",
            ""
        ])
        for component, component_score in component_scores.items():
            component_name = component.replace('_', ' ').title()
            report_lines.append(f"- {component_name}: {component_score:.1f}/100")
        
        report_lines.extend(["", "---", ""])
    
    # Recommendations section if there are failures
    if structure_missing > 0 or extraction_noisy > 0:
        report_lines.extend([
            "## Recommendations",
            "",
            _generate_recommendations(score_results),
            ""
        ])
    
    return "\n".join(report_lines)


def _identify_issues(failure_mode: str, subscores: Dict[str, float]) -> List[str]:
    """Identify specific issues based on failure mode and subscores.
    
    Args:
        failure_mode: Failure mode classification
        subscores: Component subscores
        
    Returns:
        List of issue descriptions
    """
    issues = []
    
    if failure_mode == 'structure-missing':
        semantic_score = subscores.get('semantic_structure', 0)
        hierarchy_score = subscores.get('heading_hierarchy', 0)
        
        if semantic_score < 60:
            issues.append("Missing semantic HTML elements (<main>, <article>)")
        if hierarchy_score < 80:
            issues.append("Invalid or missing heading hierarchy")
    
    elif failure_mode == 'extraction-noisy':
        density_score = subscores.get('content_density', 0)
        boilerplate_score = subscores.get('boilerplate_resistance', 0)
        
        if density_score < 60:
            issues.append("Low content density - too much non-primary content")
        if boilerplate_score < 60:
            issues.append("High boilerplate contamination from navigation/sidebar elements")
    
    return issues


def _identify_root_causes(failure_mode: str, subscores: Dict[str, float], evidence: List[str]) -> List[str]:
    """Identify root causes based on evidence.
    
    Args:
        failure_mode: Failure mode classification
        subscores: Component subscores
        evidence: List of evidence strings
        
    Returns:
        List of root cause descriptions
    """
    causes = []
    
    # Parse evidence for specific indicators
    has_main = any("main" in ev for ev in evidence)
    has_article = any("article" in ev for ev in evidence)
    no_headings = any("No headings found" in ev for ev in evidence)
    hierarchy_violations = any("hierarchy violations" in ev for ev in evidence)
    
    if failure_mode == 'structure-missing':
        if not has_main and not has_article:
            causes.append("HTML lacks semantic content containers")
        if no_headings:
            causes.append("No heading structure to indicate content organization")
        elif hierarchy_violations:
            causes.append("Heading levels jump incorrectly (e.g., H1 directly to H3)")
    
    elif failure_mode == 'extraction-noisy':
        density_score = subscores.get('content_density', 0)
        if density_score < 60:
            causes.append("Primary content not clearly distinguished from secondary content")
        
        boilerplate_score = subscores.get('boilerplate_resistance', 0)
        if boilerplate_score < 60:
            causes.append("Navigation, sidebar, or footer content overwhelms primary content")
    
    return causes


def _identify_fix_owner(failure_mode: str, subscores: Dict[str, float]) -> str:
    """Identify who likely owns the fix based on failure type.
    
    Args:
        failure_mode: Failure mode classification
        subscores: Component subscores
        
    Returns:
        Fix owner guidance
    """
    if failure_mode == 'structure-missing':
        semantic_score = subscores.get('semantic_structure', 0)
        hierarchy_score = subscores.get('heading_hierarchy', 0)
        
        if semantic_score < 40 and hierarchy_score < 50:
            return "**Frontend Developer** - HTML structure needs semantic markup and heading organization"
        elif semantic_score < 40:
            return "**Frontend Developer** - Add semantic HTML containers (<main>, <article>)"
        elif hierarchy_score < 50:
            return "**Content Author/Developer** - Fix heading hierarchy (H1→H2→H3 progression)"
    
    elif failure_mode == 'extraction-noisy':
        return "**Frontend Developer** - Improve content/chrome separation and reduce boilerplate dominance"
    
    return "**Development Team** - Review page structure and content organization"


def _generate_priority_fixes(failure_mode: str, subscores: Dict[str, float], current_score: float) -> List[Dict]:
    """Generate prioritized fixes based on impact and effort.
    
    Args:
        failure_mode: Failure mode classification
        subscores: Component subscores
        current_score: Current overall score
        
    Returns:
        List of prioritized fix dictionaries
    """
    fixes = []
    
    if failure_mode == 'structure-missing':
        semantic_score = subscores.get('semantic_structure', 0)
        hierarchy_score = subscores.get('heading_hierarchy', 0)
        
        if semantic_score < 60:
            fixes.append({
                'name': 'Add `<main>` element',
                'impact': 'High',
                'effort': 'Low',
                'score_gain': 15,
                'priority': '[CRITICAL]'
            })
            fixes.append({
                'name': 'Add `<article>` wrapper',
                'impact': 'Medium',
                'effort': 'Low',
                'score_gain': 10,
                'priority': '[IMPORTANT]'
            })
        
        if hierarchy_score < 80:
            score_gain = 12 if hierarchy_score < 50 else 8
            priority = '[CRITICAL]' if hierarchy_score < 50 else '[IMPORTANT]'
            fixes.append({
                'name': 'Fix heading hierarchy',
                'impact': 'High' if hierarchy_score < 50 else 'Medium',
                'effort': 'Medium',
                'score_gain': score_gain,
                'priority': priority
            })
    
    elif failure_mode == 'extraction-noisy':
        density_score = subscores.get('content_density', 0)
        boilerplate_score = subscores.get('boilerplate_resistance', 0)
        
        if density_score < 60:
            fixes.append({
                'name': 'Improve content density',
                'impact': 'High',
                'effort': 'Medium',
                'score_gain': 18,
                'priority': '🔥 Critical'
            })
        
        if boilerplate_score < 60:
            fixes.append({
                'name': 'Reduce boilerplate',
                'impact': 'High',
                'effort': 'High',
                'score_gain': 15,
                'priority': '📋 Planned'
            })
    
    # Sort by score gain (highest impact first)
    return sorted(fixes, key=lambda x: x['score_gain'], reverse=True)


def _generate_code_examples(failure_mode: str, subscores: Dict[str, float]) -> List[Dict]:
    """Generate HTML code examples for fixes.
    
    Args:
        failure_mode: Failure mode classification
        subscores: Component subscores
        
    Returns:
        List of code example dictionaries
    """
    examples = []
    
    if failure_mode == 'structure-missing':
        semantic_score = subscores.get('semantic_structure', 0)
        hierarchy_score = subscores.get('heading_hierarchy', 0)
        
        if semantic_score < 60:
            examples.append({
                'title': 'Add Semantic HTML Structure',
                'code': '''<!-- Before (problematic) -->
<div class="content">
  <h1>Page Title</h1>
  <p>Content here...</p>
</div>

<!-- After (semantic) -->
<main>
  <article>
    <h1>Page Title</h1>
    <p>Content here...</p>
  </article>
</main>'''
            })
        
        if hierarchy_score < 80:
            examples.append({
                'title': 'Fix Heading Hierarchy',
                'code': '''<!-- Before (hierarchy jumps) -->
<h1>Main Title</h1>
<h3>Subsection</h3>  <!-- ❌ Skip H2 -->
<h2>Section</h2>     <!-- ❌ Wrong order -->

<!-- After (proper hierarchy) -->
<h1>Main Title</h1>
<h2>Section</h2>
<h3>Subsection</h3>  <!-- ✅ Logical flow -->'''
            })
    
    elif failure_mode == 'extraction-noisy':
        density_score = subscores.get('content_density', 0)
        boilerplate_score = subscores.get('boilerplate_resistance', 0)
        
        if density_score < 60:
            examples.append({
                'title': 'Improve Content Density',
                'code': '''<!-- Before (content scattered) -->
<div class="page">
  <nav>...</nav>        <!-- Noise -->
  <aside>...</aside>    <!-- Noise -->
  <div class="content">
    <p>Main content</p>
  </div>
  <footer>...</footer>  <!-- Noise -->
</div>

<!-- After (content prioritized) -->
<div class="page">
  <main>
    <article>
      <p>Main content</p>
    </article>
  </main>
  <nav>...</nav>
  <aside>...</aside>
  <footer>...</footer>
</div>'''
            })
        
        if boilerplate_score < 60:
            examples.append({
                'title': 'Reduce Boilerplate Contamination',
                'code': '''<!-- Use semantic elements to separate content -->
<body>
  <header>Site navigation</header>
  
  <main>  <!-- ✅ Primary content area -->
    <article>
      <h1>Article Title</h1>
      <p>Article content...</p>
    </article>
  </main>
  
  <aside>Sidebar content</aside>  <!-- ✅ Secondary -->
  <footer>Footer links</footer>   <!-- ✅ Auxiliary -->
</body>'''
            })
    
    return examples


def _generate_recommendations(score_results: List[Dict]) -> str:
    """Generate overall recommendations based on failure patterns.
    
    Args:
        score_results: List of score result dictionaries
        
    Returns:
        Recommendations text
    """
    structure_issues = sum(1 for result in score_results if result['failure_mode'] == 'structure-missing')
    extraction_issues = sum(1 for result in score_results if result['failure_mode'] == 'extraction-noisy')
    
    recommendations = []
    
    if structure_issues > 0:
        recommendations.append(
            "**For structure-missing pages**: Implement semantic HTML5 elements (<main>, <article>) "
            "and ensure proper heading hierarchy (H1→H2→H3 without skipping levels)."
        )
    
    if extraction_issues > 0:
        recommendations.append(
            "**For extraction-noisy pages**: Reduce navigation/sidebar dominance by moving primary content "
            "higher in DOM order and using clearer content boundaries."
        )
    
    if len(recommendations) == 0:
        return "All pages passed evaluation. No structural improvements needed."
    
    return "\n\n".join(recommendations)