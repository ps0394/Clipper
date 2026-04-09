"""YARA 3.0 Standards-Based Scoring Engine.

API-free scoring using industry standards for agent-ready content evaluation.
Replaces API-dependent Lighthouse scoring with defensible standards methodology.
"""

import json
import os
from pathlib import Path
from typing import Optional

from .access_gate_evaluator import AccessGateEvaluator


def score_parse_results(parse_file: str, output_file: str, api_key: Optional[str] = None) -> None:
    """Score parse results using YARA 3.0 standards-based methodology.
    
    Args:
        parse_file: JSON file with parse results
        output_file: JSON file to save score results
        api_key: Deprecated parameter (YARA 3.0 is API-free)
    """
    # YARA 3.0 deprecation notice for API key
    if api_key:
        print("⚠️  API key parameter is deprecated in YARA 3.0")
        print("   YARA 3.0 uses industry standards and is completely API-free")
    
    print("🚀 YARA 3.0 Standards-Based Access Gate Evaluator")
    print("├─ WCAG 2.1 Accessibility (Deque axe-core) - 25%")
    print("├─ W3C Semantic HTML Analysis - 25%")
    print("├─ Schema.org Structured Data - 20%")
    print("├─ HTTP Standards Compliance (RFC 7231) - 15%")
    print("└─ Agent-Focused Content Quality - 15%")
    
    # Initialize standards-based evaluator
    evaluator = AccessGateEvaluator()
    
    # Load parse results
    parse_path = Path(parse_file)
    if not parse_path.exists():
        raise FileNotFoundError(f"Parse file not found: {parse_file}")
    
    with open(parse_path, 'r', encoding='utf-8') as f:
        parse_results_data = json.load(f)
    
    # Load URLs from crawl results for enhanced evaluation
    urls = _load_urls_from_crawl_results(parse_path)
    
    print(f"\n📊 Evaluating {len(parse_results_data)} documents using industry standards...")
    
    score_results = []
    for i, parse_data in enumerate(parse_results_data):
        print(f"  Standards evaluation: {parse_data['html_path']}")
        
        # Get URL for enhanced evaluation (if available)
        url = urls[i] if i < len(urls) else None
        
        # Evaluate using standards-based Access Gate methodology
        score_result = evaluator.evaluate_access_gate(parse_data, url)
        score_results.append(score_result)
    
    # Save standards-based score results
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump([result.to_dict() for result in score_results], f, indent=2, ensure_ascii=False)
    
    print(f"✅ Standards-based evaluation completed!")
    print(f"   Results saved: {output_file}")
    print(f"   Methodology: Industry standards (API-free)")


def _load_urls_from_crawl_results(parse_path: Path) -> list[str]:
    """Load URLs from crawl_results.json for enhanced evaluation."""
    
    # Try different locations for crawl_results.json
    possible_locations = [
        parse_path.parent / "crawl_results.json",
        parse_path.parent / "snapshots" / "crawl_results.json",
        parse_path.parent.parent / "crawl_results.json"
    ]
    
    for crawl_file in possible_locations:
        if crawl_file.exists():
            try:
                with open(crawl_file, 'r', encoding='utf-8') as f:
                    crawl_data = json.load(f)
                return [item['url'] for item in crawl_data]
            except Exception as e:
                print(f"Warning: Could not load URLs from {crawl_file}: {e}")
                continue
    
    print("Note: No crawl_results.json found - using static evaluation only")
    return []
