"""Clipper Standards-Based Scoring Engine.

API-free scoring using industry standards for agent-ready content evaluation.
Replaces API-dependent Lighthouse scoring with defensible standards methodology.
"""

import json
import os
from pathlib import Path
from typing import Optional

from .access_gate_evaluator import AccessGateEvaluator


def score_parse_results(parse_file: str, output_file: str, api_key: Optional[str] = None) -> None:
    """Score parse results using Clipper standards-based methodology.
    
    Args:
        parse_file: JSON file with parse results
        output_file: JSON file to save score results
        api_key: Deprecated parameter (Clipper is API-free)
    """
    # Clipper deprecation notice for API key
    if api_key:
        print("[WARN] API key parameter is deprecated in Clipper")
        print("   Clipper uses industry standards and is completely API-free")
    
    print("[CLIPPER] Standards-Based Access Gate Evaluator")
    print("|- W3C Semantic HTML Analysis - 25%")
    print("|- Content Extractability (Mozilla Readability) - 20%")
    print("|- Schema.org Structured Data - 20%")
    print("|- DOM Navigability (WCAG 2.1 / axe-core) - 15%")
    print("|- Metadata Completeness (Dublin Core / OpenGraph) - 10%")
    print("+- HTTP Compliance (RFC 7231 / robots / cache) - 10%")
    
    # Initialize standards-based evaluator
    evaluator = AccessGateEvaluator()
    
    # Load parse results
    parse_path = Path(parse_file)
    if not parse_path.exists():
        raise FileNotFoundError(f"Parse file not found: {parse_file}")
    
    with open(parse_path, 'r', encoding='utf-8') as f:
        parse_results_data = json.load(f)
    
    # Load URLs and crawl data for enhanced evaluation
    urls, crawl_results = _load_crawl_data_for_scoring(parse_path)
    
    print(f"\n📊 Evaluating {len(parse_results_data)} documents using industry standards...")
    if crawl_results:
        print(f"   Enhanced with redirect chain analysis for HTTP compliance")
    
    score_results = []
    for i, parse_data in enumerate(parse_results_data):
        print(f"  Standards evaluation: {parse_data['html_path']}")
        
        # Get URL and crawl data for enhanced evaluation (if available)
        url = urls[i] if i < len(urls) else None
        crawl_data = crawl_results[i] if i < len(crawl_results) else None
        
        # Evaluate using enhanced Access Gate methodology with redirect analysis
        score_result = evaluator.evaluate_access_gate(parse_data, url, crawl_data)
        score_results.append(score_result)
    
    # Save standards-based score results
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump([result.to_dict() for result in score_results], f, indent=2, ensure_ascii=False)
    
    print(f"✅ Standards-based evaluation completed!")
    print(f"   Results saved: {output_file}")
    print(f"   Methodology: Industry standards (API-free)")


def _load_crawl_data_for_scoring(parse_path: Path) -> tuple[list[str], list[dict]]:
    """Load URLs and crawl data from crawl_results.json for enhanced evaluation.
    
    Returns:
        Tuple of (urls_list, crawl_results_list) for redirect analysis
    """
    
    # Try different locations for crawl_results.json
    possible_locations = [
        parse_path.parent / "crawl_results.json",
        parse_path.parent / "snapshots" / "crawl_results.json",
    ]
    
    crawl_results_path = None
    for location in possible_locations:
        if location.exists():
            crawl_results_path = location
            break
    
    if not crawl_results_path:
        print("   [INFO] No crawl_results.json found - redirect analysis will use fallback scoring")
        return [], []
    
    try:
        with open(crawl_results_path, 'r', encoding='utf-8') as f:
            crawl_data = json.load(f)
        
        urls = [result['url'] for result in crawl_data]
        
        # Extract crawl results with redirect chain data
        crawl_results = []
        for result in crawl_data:
            crawl_info = {
                'redirect_chain': result.get('redirect_chain', []),
                'redirect_count': result.get('redirect_count', 0),
                'total_redirect_time_ms': result.get('total_redirect_time_ms', 0.0),
                'final_response_time_ms': result.get('final_response_time_ms', 0.0),
                'final_url': result.get('final_url', result['url']),
                'status': result.get('status', 200)
            }
            crawl_results.append(crawl_info)
        
        print(f"   [INFO] Loaded {len(crawl_results)} crawl results with redirect data")
        redirect_sites = sum(1 for r in crawl_results if r['redirect_count'] > 0)
        if redirect_sites > 0:
            print(f"   [INFO] Found {redirect_sites} sites with redirects for enhanced HTTP compliance scoring")
        
        return urls, crawl_results
        
    except Exception as e:
        print(f"   [WARN] Failed to load crawl results: {e}")
        return [], []
