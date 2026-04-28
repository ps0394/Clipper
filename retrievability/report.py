"""Report generation for retrievability evaluation results."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime

from .schemas import ScoreResult


# Canonical pillar order and default (article-profile) weights used for
# rough template-cluster uplift estimates. Matching the evaluator's article
# profile keeps cross-report numbers consistent without introducing a
# profile-aware report layer.
_PILLAR_ORDER: Tuple[str, ...] = (
    'semantic_html',
    'content_extractability',
    'structured_data',
    'dom_navigability',
    'metadata_completeness',
    'http_compliance',
)
_PILLAR_WEIGHTS: Dict[str, float] = {
    'semantic_html': 0.25,
    'content_extractability': 0.20,
    'structured_data': 0.20,
    'dom_navigability': 0.15,
    'metadata_completeness': 0.10,
    'http_compliance': 0.10,
}
_CLUSTER_MIN_MEMBERS = 3
_TEMPLATE_UPLIFT_TARGET = 70.0  # Score a weak pillar is assumed to reach once fixed.
_TEMPLATE_WEAK_PILLAR_THRESHOLD = 70.0  # Pillar avg below this is flagged in a cluster.

# Phase 3.1 rendering-mode delta thresholds.
_RENDER_DELTA_FLAG_THRESHOLD = 15.0   # |rendered - raw| >= this is flagged as JS-dependent.


def _page_identifier(result: Dict, fallback_index: int) -> str:
    """Prefer URL if available, otherwise html_path, otherwise a stable index."""
    return result.get('url') or result.get('html_path') or f'Page {fallback_index}'


def _cluster_signature(component_scores: Dict) -> Optional[Tuple[int, ...]]:
    """Round each pillar to the nearest integer to form a cluster key.

    Returns None if any pillar in the canonical order is missing (which
    happens in partial evaluations — those pages should not be clustered
    against fully-scored ones).
    """
    signature = []
    for pillar in _PILLAR_ORDER:
        value = component_scores.get(pillar)
        if value is None:
            return None
        signature.append(int(round(float(value))))
    return tuple(signature)


def _detect_template_clusters(score_results: List[Dict]) -> List[Dict]:
    """Find per-pillar score clusters that indicate CMS template issues.

    Full-tuple matches (all six pillars identical within 1pt) are rare on
    heterogeneous corpora. The real template signal is *per-pillar*: when
    N pages score exactly the same on one pillar, the shared weakness
    almost certainly lives in the shared template rather than in page
    authoring. A cluster here is therefore a (pillar, rounded_score, pages)
    tuple with at least ``_CLUSTER_MIN_MEMBERS`` members.

    We only surface clusters where the shared score is below
    ``_TEMPLATE_WEAK_PILLAR_THRESHOLD`` — a shared *good* score is not a
    finding to act on.

    Returns a list of cluster dicts sorted by (members desc, uplift desc),
    each with:

    - ``pillar``: the pillar name whose score is shared.
    - ``shared_score``: the rounded 0-100 score shared across members.
    - ``members``: list of original indices into ``score_results``.
    - ``pages``: list of human-readable identifiers.
    - ``estimated_uplift``: rough per-page gain if this one pillar were
      lifted from ``shared_score`` to ``_TEMPLATE_UPLIFT_TARGET``,
      weighted by the default article profile.
    """
    # buckets[pillar][rounded_score] -> list of (index, raw_score)
    buckets: Dict[str, Dict[int, List[int]]] = {p: {} for p in _PILLAR_ORDER}
    for idx, result in enumerate(score_results):
        scores = result.get('component_scores', result.get('subscores', {})) or {}
        for pillar in _PILLAR_ORDER:
            value = scores.get(pillar)
            if value is None:
                continue  # partial evaluations skipped for this pillar
            key = int(round(float(value)))
            buckets[pillar].setdefault(key, []).append(idx)

    clusters: List[Dict] = []
    for pillar, by_score in buckets.items():
        for shared_score, members in by_score.items():
            if len(members) < _CLUSTER_MIN_MEMBERS:
                continue
            if shared_score >= _TEMPLATE_WEAK_PILLAR_THRESHOLD:
                continue  # shared *good* score is not a finding to act on
            uplift = (_TEMPLATE_UPLIFT_TARGET - shared_score) * _PILLAR_WEIGHTS[pillar]
            clusters.append({
                'pillar': pillar,
                'shared_score': shared_score,
                'members': members,
                'pages': [_page_identifier(score_results[m], m + 1) for m in members],
                'estimated_uplift': uplift,
            })

    clusters.sort(key=lambda c: (-len(c['members']), -c['estimated_uplift']))
    return clusters


def _profile_of(result: Dict) -> str:
    """Extract the detected content-type profile from a ScoreResult dict.

    Falls back to ``'article'`` (the default profile) when content-type
    detection metadata is missing, which matches the evaluator's own
    fallback when no signal is present.
    """
    ct = result.get('audit_trail', {}).get('_content_type', {})
    return ct.get('profile', 'article') if isinstance(ct, dict) else 'article'


def _format_profile_impact_section(results: List[Dict]) -> List[str]:
    """Produce the 'Profile Impact' section showing universal vs
    profile-adjusted scores per URL.

    The section is emitted only when at least one page was scored under a
    non-default profile AND at least one page has a universal_score
    recorded. This keeps single-profile runs from printing a redundant
    table where every row reads "delta 0.0".
    """
    rows: List[Dict] = []
    non_default_seen = False
    for r in results:
        universal = r.get('universal_score')
        if universal is None:
            continue
        profile = _profile_of(r)
        if profile != 'article':
            non_default_seen = True
        parseability = float(r.get('parseability_score') or 0.0)
        universal = float(universal)
        rows.append({
            'url': r.get('url') or r.get('html_path') or '',
            'profile': profile,
            'parseability': parseability,
            'universal': universal,
            'delta': parseability - universal,
        })

    if not rows or not non_default_seen:
        return []

    # Sort by absolute delta descending so the most profile-sensitive pages
    # surface first.
    rows.sort(key=lambda r: -abs(r['delta']))

    lines: List[str] = [
        "## Profile Impact",
        "",
        (
            "Each page is scored twice: **Profile** uses the weights for the "
            "detected content type (the headline `parseability_score`), and "
            "**Universal** uses the default article weights (the "
            "`universal_score`). The delta reveals how much the content-type "
            "profile is moving each page's headline number. Large deltas "
            "mean the classifier's call is doing real work — good for "
            "legibility, and a risk if the classification is wrong."
        ),
        "",
        "| URL | Profile | Profile Score | Universal Score | Delta |",
        "|-----|---------|---------------|-----------------|-------|",
    ]
    for row in rows:
        lines.append(
            f"| {row['url']} "
            f"| `{row['profile']}` "
            f"| {row['parseability']:.1f} "
            f"| {row['universal']:.1f} "
            f"| {row['delta']:+.1f} |"
        )
    lines.append("")
    return lines


def _format_template_section(clusters: List[Dict]) -> List[str]:
    """Produce the top 'Template Findings' section markdown lines."""
    if not clusters:
        return []

    total_affected = sum(len(c['members']) for c in clusters)
    lines: List[str] = [
        "## Template Findings",
        "",
        (
            f"Detected {len(clusters)} template-level cluster"
            f"{'s' if len(clusters) != 1 else ''} covering "
            f"{total_affected} page-pillar pair"
            f"{'s' if total_affected != 1 else ''}. "
            "Each cluster is a group of pages sharing exactly the same low "
            "score on one pillar (within 1 point), which almost always "
            "means the shared weakness lives in the CMS template rather "
            "than in page authoring. Fixing the template lifts every page "
            "in the cluster simultaneously."
        ),
        "",
        "| # | Pillar | Shared Score | Pages | Est. Uplift per Page |",
        "|---|--------|--------------|-------|----------------------|",
    ]
    for i, cluster in enumerate(clusters, 1):
        lines.append(
            f"| {i} | `{cluster['pillar']}` "
            f"| {cluster['shared_score']}/100 "
            f"| {len(cluster['members'])} "
            f"| +{cluster['estimated_uplift']:.1f} pts |"
        )
    lines.append("")

    for i, cluster in enumerate(clusters, 1):
        lines.extend([
            f"### Cluster {i}: `{cluster['pillar']}` = {cluster['shared_score']}/100 "
            f"({len(cluster['members'])} pages)",
            "",
            (
                f"- **Finding:** every page below scores exactly "
                f"{cluster['shared_score']}/100 on `{cluster['pillar']}`. "
                "This is a template-level signal."
            ),
            (
                f"- **Estimated uplift:** lifting this pillar to "
                f"{_TEMPLATE_UPLIFT_TARGET:.0f}/100 adds "
                f"~{cluster['estimated_uplift']:.1f} points to each affected page."
            ),
            "- **Affected pages:**",
        ])
        for page in cluster['pages']:
            lines.append(f"  - {page}")
        lines.append("")

    return lines


def _detect_render_deltas(score_results: List[Dict]) -> List[Dict]:
    """Match raw/rendered ScoreResult pairs by URL and compute deltas.

    Returns a list of dicts ordered by absolute delta (descending), each
    with ``url``, ``raw_score``, ``rendered_score``, ``delta`` (rendered -
    raw), and ``flagged`` (``abs(delta) >= _RENDER_DELTA_FLAG_THRESHOLD``).

    Returns an empty list when the evaluation produced only one mode
    (``render_mode == 'raw'`` or ``'rendered'`` alone), which is the common
    single-mode case.
    """
    by_url: Dict[str, Dict[str, float]] = {}
    for r in score_results:
        url = r.get('url') or r.get('html_path') or ''
        mode = r.get('render_mode', 'rendered')
        if not url:
            continue
        by_url.setdefault(url, {})[mode] = float(r.get('parseability_score') or 0.0)

    deltas: List[Dict] = []
    for url, by_mode in by_url.items():
        if 'raw' not in by_mode or 'rendered' not in by_mode:
            continue
        raw = by_mode['raw']
        rendered = by_mode['rendered']
        delta = rendered - raw
        deltas.append({
            'url': url,
            'raw_score': raw,
            'rendered_score': rendered,
            'delta': delta,
            'flagged': abs(delta) >= _RENDER_DELTA_FLAG_THRESHOLD,
        })

    deltas.sort(key=lambda d: -abs(d['delta']))
    return deltas


def _format_render_delta_section(deltas: List[Dict]) -> List[str]:
    """Produce the 'Rendering-Mode Deltas' section markdown lines."""
    if not deltas:
        return []

    flagged = [d for d in deltas if d['flagged']]
    lines: List[str] = [
        "## Rendering-Mode Deltas",
        "",
        (
            f"Evaluated {len(deltas)} URL"
            f"{'s' if len(deltas) != 1 else ''} in both `raw` and `rendered` "
            "modes. Raw mode models agents that do not execute JavaScript "
            "(RAG crawlers, search indexers, API clients); rendered mode "
            "models agents that see the post-JS DOM. A large delta means "
            "the page relies on JavaScript for content that non-JS agents "
            "cannot reach."
        ),
        "",
        f"**JS-dependent pages** (|delta| >= {_RENDER_DELTA_FLAG_THRESHOLD:.0f}): "
        f"{len(flagged)}",
        "",
        "| URL | Raw | Rendered | Delta |",
        "|-----|-----|----------|-------|",
    ]
    for d in deltas:
        flag = " [FLAG]" if d['flagged'] else ""
        lines.append(
            f"| {d['url']} "
            f"| {d['raw_score']:.1f} "
            f"| {d['rendered_score']:.1f} "
            f"| {d['delta']:+.1f}{flag} |"
        )
    lines.append("")
    return lines


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

    # If render_mode='both' was used, the input list contains two entries
    # per URL. Compute deltas up front; summary stats below use the
    # rendered-mode entries (plus single-mode entries) so counts reflect
    # pages rather than (page, mode) pairs.
    render_deltas = _detect_render_deltas(score_results)
    has_both_modes = bool(render_deltas)
    if has_both_modes:
        # Canonical list for summary: prefer 'rendered' entries, fall back
        # to whatever is present for single-mode pages.
        by_url_mode: Dict[Tuple[str, str], Dict] = {}
        for r in score_results:
            key = (r.get('url') or r.get('html_path') or '', r.get('render_mode', 'rendered'))
            by_url_mode[key] = r
        summary_results: List[Dict] = []
        seen_urls: Set[str] = set()
        for r in score_results:
            url = r.get('url') or r.get('html_path') or ''
            if url in seen_urls:
                continue
            seen_urls.add(url)
            rendered_entry = by_url_mode.get((url, 'rendered'), r)
            summary_results.append(rendered_entry)
    else:
        summary_results = score_results

    # Calculate summary statistics (one row per URL, not per mode)
    total_pages = len(summary_results)
    clean_pages = sum(1 for result in summary_results if result['failure_mode'] == 'clean')
    structure_missing = sum(1 for result in summary_results if result['failure_mode'] == 'structure-missing')
    extraction_noisy = sum(1 for result in summary_results if result['failure_mode'] == 'extraction-noisy')

    avg_score = sum((result.get('parseability_score') or 0.0) for result in summary_results) / total_pages if total_pages > 0 else 0
    
    # Build report sections
    report_lines = []

    # v2.1 — Methodology disclosure banner. Always emit when present in
    # input; flag diagnostic mode prominently when composites are nulled.
    diagnostic_mode = any(bool(r.get('diagnostic_mode')) for r in score_results)
    methodology = next(
        (r.get('methodology') for r in score_results if isinstance(r.get('methodology'), dict)),
        None,
    )
    if diagnostic_mode or methodology:
        report_lines.append("> **Methodology disclosure (v2.1):** "
                            + (methodology or {}).get('generalization_status',
                                                      'see findings/post-v2-roadmap.md'))
        if diagnostic_mode:
            report_lines.append("> ")
            report_lines.append("> **Diagnostic mode is ON.** "
                                "Composite scores (`parseability_score`, "
                                "`universal_score`) are suppressed in the "
                                "JSON output. Pillar-level scores below "
                                "remain valid and are the recommended "
                                "basis for comparison.")
        report_lines.append("")

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

    # Rendering-mode deltas (Phase 3.1): shown only when render_mode='both'
    # was used and the input actually contains paired results.
    report_lines.extend(_format_render_delta_section(render_deltas))

    # Profile impact: surface universal vs profile-adjusted scores so the
    # content-type classifier's contribution to the headline number is
    # legible. Only emitted when at least one page was scored under a
    # non-default profile.
    report_lines.extend(_format_profile_impact_section(summary_results))

    # Template findings (Phase 2.1): group URLs sharing low scores on the
    # same pillar. Only meaningful for multi-URL evaluations.
    clusters = _detect_template_clusters(summary_results) if total_pages >= _CLUSTER_MIN_MEMBERS else []
    # Map index -> set of pillars flagged at the template level for that page.
    page_template_pillars: Dict[int, Set[str]] = {}
    for cluster in clusters:
        for m in cluster['members']:
            page_template_pillars.setdefault(m, set()).add(cluster['pillar'])
    report_lines.extend(_format_template_section(clusters))

    # Individual page results
    if clusters:
        report_lines.extend([
            "## Page-Specific Findings",
            "",
            (
                "Pillars already flagged in **Template Findings** above are "
                "noted per page rather than re-explained. Focus this section "
                "on variation that is *not* template-driven."
            ),
            "",
        ])
    else:
        report_lines.extend([
            "## Individual Page Results",
            ""
        ])

    # Sort by score (lowest first - most problematic)
    indexed_results = list(enumerate(summary_results))
    sorted_results = sorted(indexed_results, key=lambda x: (x[1].get('parseability_score') or 0.0))

    for display_index, (original_idx, result) in enumerate(sorted_results, 1):
        score = result.get('parseability_score') or 0.0
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
        page_id = _page_identifier(result, display_index)
        
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
        ])

        # Headline score line: when the page was scored under a non-default
        # profile, show both the profile-adjusted score (the headline
        # parseability_score) and the universal/article-default score.
        # Otherwise keep the historical single-number line so article-only
        # runs stay compact.
        profile = _profile_of(result)
        universal = result.get('universal_score')
        if profile != 'article' and universal is not None:
            delta = score - float(universal)
            report_lines.extend([
                (
                    f"**Overall Score**: {score:.1f}/100 "
                    f"(profile `{profile}`) — universal {float(universal):.1f}/100 "
                    f"({delta:+.1f})"
                ),
                f"**Failure Mode**: `{failure_mode}`",
                "",
            ])
        else:
            report_lines.extend([
                f"**Overall Score**: {score:.1f}/100",
                f"**Failure Mode**: `{failure_mode}`",
                "",
            ])

        # Phase 2.1: note which pillars on this page are already flagged at
        # the template level, so readers don't re-diagnose them per page.
        template_pillars_for_page = page_template_pillars.get(original_idx, set())
        if template_pillars_for_page:
            pillar_list = ", ".join(
                f"`{p}`" for p in _PILLAR_ORDER if p in template_pillars_for_page
            )
            report_lines.extend([
                f"**Template-covered pillars:** {pillar_list} — see **Template Findings** above.",
                "",
            ])

        # Phase 3.1: if this URL has both raw and rendered scores, note the
        # delta next to the headline score so readers see the JS impact.
        if has_both_modes:
            page_url = result.get('url') or result.get('html_path') or ''
            delta_entry = next((d for d in render_deltas if d['url'] == page_url), None)
            if delta_entry:
                flag_text = " — **JS-dependent**" if delta_entry['flagged'] else ""
                report_lines.extend([
                    (
                        f"**Rendering Delta:** raw {delta_entry['raw_score']:.1f} -> "
                        f"rendered {delta_entry['rendered_score']:.1f} "
                        f"({delta_entry['delta']:+.1f}){flag_text}"
                    ),
                    "",
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