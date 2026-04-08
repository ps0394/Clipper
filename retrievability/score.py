"""Scoring and failure mode classification for parseability signals."""

import json
from pathlib import Path
from typing import Dict, List, Optional
import math
import os

from .schemas import ScoreResult, ParseResult
from .hybrid_score import HybridScorer


def score_parse_results(parse_file: str, output_file: str, use_hybrid: bool = True, 
                       api_key: Optional[str] = None) -> None:
    """Score parse results using YARA 2.0 hybrid methodology or legacy YARA.
    
    Args:
        parse_file: JSON file with parse results
        output_file: JSON file to save score results
        use_hybrid: Use YARA 2.0 hybrid scoring (default: True)
        api_key: PageSpeed Insights API key for Lighthouse analysis
    """
    # Check for API key in environment if not provided
    if not api_key:
        api_key = os.environ.get('PAGESPEED_API_KEY')
    
    # Use hybrid scoring by default (YARA 2.0)
    if use_hybrid:
        print("🚀 Using YARA 2.0 Hybrid Scoring Engine")
        hybrid_scorer = HybridScorer(pagespeed_api_key=api_key)
        hybrid_scorer.score_parse_results(parse_file, output_file)
        return
    
    # Legacy YARA scoring (deprecated)
    print("⚠️  Using Legacy YARA Scoring (deprecated - consider --hybrid)")
    parse_path = Path(parse_file)
    if not parse_path.exists():
        raise FileNotFoundError(f"Parse file not found: {parse_file}")
    
    with open(parse_path, 'r', encoding='utf-8') as f:
        parse_results_data = json.load(f)
    
    # Convert to ParseResult objects
    parse_results = []
    for data in parse_results_data:
        # Reconstruct ParseResult from dict (simplified)
        parse_results.append(data)
    
    score_results = []
    
    for parse_data in parse_results:
        print(f"Scoring: {parse_data['html_path']}")
        score_result = _score_parse_result(parse_data)
        score_results.append(score_result)
    
    # Save score results
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump([result.to_dict() for result in score_results], f, indent=2)
    
    print(f"Scored {len(score_results)} parse results, results saved to {output_file}")


def _score_parse_result(parse_data: Dict) -> ScoreResult:
    """Score a single parse result.
    
    Args:
        parse_data: Dictionary containing parse result data
        
    Returns:
        ScoreResult with scores and failure mode classification
    """
    signals = parse_data['signals']
    evidence = parse_data['evidence']
    
    # Calculate component subscores (0-100 scale)
    subscores = _calculate_subscores(signals, evidence)
    
    # Calculate overall parseability score (weighted average)
    parseability_score = _calculate_overall_score(subscores)
    
    # Classify failure mode based on signals and scores
    failure_mode = _classify_failure_mode(signals, subscores, parseability_score)
    
    # Gather evidence references
    evidence_refs = _gather_evidence_references(signals, evidence)
    
    return ScoreResult(
        parseability_score=parseability_score,
        failure_mode=failure_mode,
        subscores=subscores,
        evidence_references=evidence_refs
    )


def _calculate_subscores(signals: Dict, evidence: Dict) -> Dict[str, float]:
    """Calculate component subscores from signals.
    
    Args:
        signals: Dictionary of parseability signals
        evidence: Dictionary of evidence data
        
    Returns:
        Dictionary of subscore components (0-100 scale)
    """
    subscores = {}
    
    # Semantic structure score (presence of main/article elements)
    semantic_score = 0.0
    if signals['has_main_element']:
        semantic_score += 60.0
    if signals['has_article_element']:
        semantic_score += 40.0
    subscores['semantic_structure'] = min(semantic_score, 100.0)
    
    # Heading hierarchy score
    if signals['heading_hierarchy_valid']:
        hierarchy_score = 100.0
    else:
        # Partial credit based on heading presence
        heading_count = len(evidence.get('heading_structure', []))
        if heading_count > 0:
            hierarchy_score = 30.0  # Some structure present but invalid
        else:
            hierarchy_score = 0.0   # No headings at all
    subscores['heading_hierarchy'] = hierarchy_score
    
    # Content density score (higher text density = better)
    density_ratio = signals['text_density_ratio']
    density_score = min(density_ratio * 100.0, 100.0)
    subscores['content_density'] = density_score
    
    # Rich content score (presence of code blocks, tables)
    rich_content_score = 0.0
    if signals['code_blocks_count'] > 0:
        rich_content_score += 50.0
    if signals['tables_count'] > 0:
        rich_content_score += 50.0
    subscores['rich_content'] = min(rich_content_score, 100.0)
    
    # Boilerplate contamination score (lower leakage = better)
    boilerplate_ratio = signals['boilerplate_leakage_estimate']
    contamination_score = max(100.0 - (boilerplate_ratio * 100.0), 0.0)
    subscores['boilerplate_resistance'] = contamination_score
    
    return subscores


def _calculate_overall_score(subscores: Dict[str, float]) -> float:
    """Calculate weighted overall parseability score.
    
    Args:
        subscores: Dictionary of component subscores
        
    Returns:
        Overall parseability score (0-100)
    """
    # Weights for different components (must sum to 1.0)
    weights = {
        'semantic_structure': 0.25,     # Critical for extraction
        'heading_hierarchy': 0.20,      # Important for structure
        'content_density': 0.25,        # Core content signal
        'rich_content': 0.10,           # Nice to have
        'boilerplate_resistance': 0.20  # Important for clean extraction
    }
    
    weighted_sum = 0.0
    total_weight = 0.0
    
    for component, weight in weights.items():
        if component in subscores:
            weighted_sum += subscores[component] * weight
            total_weight += weight
    
    # Normalize by actual weights used
    if total_weight > 0:
        return weighted_sum / total_weight
    else:
        return 0.0


def _classify_failure_mode(signals: Dict, subscores: Dict[str, float], overall_score: float) -> str:
    """Classify failure mode based on signals and scores.
    
    Args:
        signals: Dictionary of parseability signals
        subscores: Dictionary of component subscores  
        overall_score: Overall parseability score
        
    Returns:
        Failure mode classification: 'clean' | 'structure-missing' | 'extraction-noisy'
    """
    # Thresholds for classification
    CLEAN_THRESHOLD = 80.0
    STRUCTURE_THRESHOLD = 50.0
    
    # Clean: High overall score with good structure
    if overall_score >= CLEAN_THRESHOLD:
        semantic_score = subscores.get('semantic_structure', 0.0)
        hierarchy_score = subscores.get('heading_hierarchy', 0.0)
        
        if semantic_score >= 60.0 and hierarchy_score >= 80.0:
            return 'clean'
    
    # Structure-missing: Low semantic/hierarchy scores
    semantic_score = subscores.get('semantic_structure', 0.0)
    hierarchy_score = subscores.get('heading_hierarchy', 0.0)
    
    if semantic_score < 40.0 or hierarchy_score < STRUCTURE_THRESHOLD:
        return 'structure-missing'
    
    # Extraction-noisy: Decent structure but poor content/boilerplate scores
    density_score = subscores.get('content_density', 0.0)
    boilerplate_score = subscores.get('boilerplate_resistance', 0.0)
    
    if density_score < 60.0 or boilerplate_score < 60.0:
        return 'extraction-noisy'
    
    # Default fallback
    if overall_score >= STRUCTURE_THRESHOLD:
        return 'extraction-noisy'
    else:
        return 'structure-missing'


def _gather_evidence_references(signals: Dict, evidence: Dict) -> List[str]:
    """Gather references to evidence supporting the scores.
    
    Args:
        signals: Dictionary of parseability signals
        evidence: Dictionary of evidence data
        
    Returns:
        List of evidence reference strings
    """
    refs = []
    
    # Semantic structure evidence
    semantic_elements = evidence.get('semantic_elements', {})
    main_count = semantic_elements.get('main_count', 0)
    article_count = semantic_elements.get('article_count', 0)
    
    if main_count > 0:
        refs.append(f"Found {main_count} <main> element(s)")
    if article_count > 0:
        refs.append(f"Found {article_count} <article> element(s)")
        
    # Heading structure evidence
    headings = evidence.get('heading_structure', [])
    if headings:
        refs.append(f"Heading structure: {len(headings)} headings detected")
        if not signals['heading_hierarchy_valid']:
            refs.append("Heading hierarchy violations detected")
    else:
        refs.append("No headings found")
    
    # Content structure evidence
    content_structure = evidence.get('content_structure', {})
    code_count = content_structure.get('code_elements', 0)
    table_count = content_structure.get('table_elements', 0)
    
    if code_count > 0:
        refs.append(f"Found {code_count} code element(s)")
    if table_count > 0:
        refs.append(f"Found {table_count} table element(s)")
    
    # Text density evidence
    density_ratio = signals['text_density_ratio']
    refs.append(f"Content density ratio: {density_ratio:.2f}")
    
    # Boilerplate evidence
    boilerplate_ratio = signals['boilerplate_leakage_estimate']
    refs.append(f"Boilerplate leakage estimate: {boilerplate_ratio:.2f}")
    
    return refs