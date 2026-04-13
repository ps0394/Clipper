#!/usr/bin/env python3
"""Benchmark validation suite for YARA evaluations."""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class BenchmarkExpectation:
    url: str
    expected_min: float
    expected_max: float
    rationale: str
    category: str

@dataclass
class ValidationResult:
    url: str
    expected_range: Tuple[float, float]
    actual_score: float
    passes: bool
    deviation: float
    rationale: str

# Curated benchmark dataset with expected score ranges
BENCHMARK_DATA = [
    # Champions - Should score 80-100 (clean)
    BenchmarkExpectation(
        "https://docs.github.com/en", 80, 100,
        "Perfect semantic HTML5 with main/article elements, clean hierarchy",
        "champion"
    ),
    BenchmarkExpectation(
        "https://learn.microsoft.com/en-us/azure/", 80, 95,
        "Excellent semantic structure, proper headings, rich content",
        "champion"
    ),
    BenchmarkExpectation(
        "https://developer.mozilla.org/en-US/docs/Web/HTML", 75, 95,
        "Strong semantic markup, code examples, good hierarchy",
        "champion"
    ),
    
    # Problematic - Should score 20-50 (structure-missing or extraction-noisy)
    BenchmarkExpectation(
        "https://stackoverflow.com/questions/tagged/azure", 20, 50,
        "Poor semantic structure, high boilerplate, complex layout",
        "problematic"
    ),
    BenchmarkExpectation(
        "https://reddit.com/r/programming", 25, 45,
        "Minimal semantic markup, high noise-to-signal ratio",
        "problematic"
    ),
    
    # Decent - Should score 50-80 (extraction-noisy)
    BenchmarkExpectation(
        "https://en.wikipedia.org/wiki/Cloud_computing", 60, 85,
        "Good semantic structure but some boilerplate leakage",
        "decent"
    ),
    BenchmarkExpectation(
        "https://cloud.google.com/functions/docs/concepts/overview", 45, 75,
        "Decent content but potential structure issues",
        "decent"
    ),
    
    # Edge Cases - Variable scores depending on implementation
    BenchmarkExpectation(
        "https://news.ycombinator.com", 30, 60,
        "Minimal semantic markup, varies by content density",
        "edge_case"
    ),
]


def load_yara_results(results_file: str) -> Dict[str, float]:
    """Load YARA evaluation results from JSON file."""
    
    # Try to load scores.json format first
    scores_file = Path(results_file)
    if scores_file.name == 'scores.json' or 'scores' in scores_file.name:
        with open(scores_file) as f:
            scores_data = json.load(f)
        
        # Need to get URLs from crawl_results.json
        crawl_file = scores_file.parent / "crawl_results.json"
        if not crawl_file.exists():
            crawl_file = scores_file.parent / "snapshots" / "crawl_results.json"
        
        if crawl_file.exists():
            with open(crawl_file) as f:
                crawl_data = json.load(f)
                urls = [result['url'] for result in crawl_data]
        else:
            raise FileNotFoundError(f"Cannot find crawl_results.json to match URLs with scores")
        
        # Combine URLs with scores
        results = {}
        for i, score_data in enumerate(scores_data):
            if i < len(urls):
                results[urls[i]] = score_data['parseability_score']
        
        return results
    
    # Fallback for other formats
    with open(results_file) as f:
        data = json.load(f)
    
    # Extract URL -> score mapping (adapt based on actual format)
    if isinstance(data, list) and data and 'url' in data[0]:
        return {item['url']: item['parseability_score'] for item in data}
    else:
        raise ValueError(f"Unsupported results format in {results_file}")


def validate_benchmark(results: Dict[str, float]) -> List[ValidationResult]:
    """Validate YARA results against benchmark expectations."""
    
    validation_results = []
    
    for benchmark in BENCHMARK_DATA:
        if benchmark.url in results:
            actual_score = results[benchmark.url]
            expected_range = (benchmark.expected_min, benchmark.expected_max)
            
            passes = benchmark.expected_min <= actual_score <= benchmark.expected_max
            
            if not passes:
                if actual_score > benchmark.expected_max:
                    deviation = actual_score - benchmark.expected_max
                else:
                    deviation = benchmark.expected_min - actual_score
            else:
                deviation = 0.0
            
            validation_results.append(ValidationResult(
                url=benchmark.url,
                expected_range=expected_range,
                actual_score=actual_score,
                passes=passes,
                deviation=deviation,
                rationale=benchmark.rationale
            ))
    
    return validation_results


def generate_validation_report(validation_results: List[ValidationResult]) -> str:
    """Generate human-readable validation report."""
    
    total = len(validation_results)
    passed = sum(1 for r in validation_results if r.passes)
    failed = total - passed
    
    report = [
        "# YARA Benchmark Validation Report",
        f"**Date:** {Path.cwd()}",
        f"**Results:** {passed}/{total} passed ({passed/total*100:.1f}%)",
        ""
    ]
    
    if failed > 0:
        report.extend([
            "## ❌ Failed Validations",
            ""
        ])
        
        for result in validation_results:
            if not result.passes:
                report.extend([
                    f"### {result.url}",
                    f"- **Expected:** {result.expected_range[0]}-{result.expected_range[1]}",
                    f"- **Actual:** {result.actual_score:.1f}",
                    f"- **Deviation:** {result.deviation:.1f} points",
                    f"- **Rationale:** {result.rationale}",
                    ""
                ])
    
    if passed > 0:
        report.extend([
            "## ✅ Passed Validations",
            ""
        ])
        
        for result in validation_results:
            if result.passes:
                report.append(f"- **{result.url}:** {result.actual_score:.1f} (expected {result.expected_range[0]}-{result.expected_range[1]})")
        
        report.append("")
    
    # Summary by category
    by_category = {}
    for result in validation_results:
        # Find category from benchmark data
        category = next((b.category for b in BENCHMARK_DATA if b.url == result.url), "unknown")
        if category not in by_category:
            by_category[category] = {"passed": 0, "total": 0}
        by_category[category]["total"] += 1
        if result.passes:
            by_category[category]["passed"] += 1
    
    report.extend([
        "## 📊 Summary by Category",
        ""
    ])
    
    for category, stats in by_category.items():
        accuracy = stats["passed"] / stats["total"] * 100
        report.append(f"- **{category.title()}:** {stats['passed']}/{stats['total']} ({accuracy:.1f}%)")
    
    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="Validate YARA results against benchmark expectations")
    parser.add_argument("results_file", help="JSON file with YARA evaluation results")
    parser.add_argument("--fail-threshold", type=float, default=20.0, 
                       help="Fail if any deviation exceeds this threshold (default: 20.0)")
    parser.add_argument("--accuracy-threshold", type=float, default=0.7,
                       help="Fail if overall accuracy below this ratio (default: 0.7)")
    parser.add_argument("--output", help="Save validation report to file")
    parser.add_argument("--quiet", action="store_true", help="Only print summary")
    
    args = parser.parse_args()
    
    try:
        # Load YARA results
        results = load_yara_results(args.results_file)
        if not args.quiet:
            print(f"Loaded {len(results)} YARA results")
        
        # Validate against benchmark
        validation_results = validate_benchmark(results)
        
        if not validation_results:
            print("⚠️  No benchmark URLs found in results")
            return 1
        
        # Generate report
        report = generate_validation_report(validation_results)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"📄 Validation report saved to {args.output}")
        
        if not args.quiet:
            print(report)
        
        # Check failure conditions
        total = len(validation_results)
        passed = sum(1 for r in validation_results if r.passes)
        accuracy = passed / total
        
        max_deviation = max((r.deviation for r in validation_results), default=0)
        
        if accuracy < args.accuracy_threshold:
            print(f"❌ FAIL: Accuracy {accuracy:.1%} below threshold {args.accuracy_threshold:.1%}")
            return 1
        
        if max_deviation > args.fail_threshold:
            print(f"❌ FAIL: Max deviation {max_deviation:.1f} exceeds threshold {args.fail_threshold}")
            return 1
        
        print(f"✅ PASS: {passed}/{total} validations passed ({accuracy:.1%})")
        return 0
    
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())