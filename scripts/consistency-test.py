#!/usr/bin/env python3
"""Test Clipper consistency by running same URLs multiple times."""

import json
import argparse
import tempfile
import subprocess
from pathlib import Path
from statistics import mean, stdev
from typing import Dict, List, Tuple

def run_clipper_evaluation(urls_file: str, run_id: int, quiet: bool = True) -> Dict[str, float]:
    """Run Clipper evaluation and return URL -> score mapping."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / f"consistency-run-{run_id}"
        
        # Run Clipper express command
        cmd = [
            "python", "-m", "retrievability.cli", "express",
            urls_file,
            "--out", str(output_dir),
            "--name", f"run{run_id}"
        ]
        
        if quiet:
            cmd.extend(["--quiet"])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Load results
            scores_file = output_dir / f"run{run_id}_scores.json" 
            crawl_file = output_dir / "snapshots" / "crawl_results.json"
            
            # Get URLs
            with open(crawl_file) as f:
                crawl_data = json.load(f)
                urls = [item['url'] for item in crawl_data]
            
            # Get scores  
            with open(scores_file) as f:
                scores_data = json.load(f)
                scores = [item['parseability_score'] for item in scores_data]
            
            return dict(zip(urls, scores))
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Run {run_id} failed: {e.stderr}")
            return {}


def analyze_consistency(results: List[Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    """Analyze consistency across multiple runs."""
    
    # Get all URLs that appear in all runs
    all_urls = set()
    for result in results:
        all_urls.update(result.keys())
    
    consistent_urls = all_urls
    for result in results:
        consistent_urls &= set(result.keys())
    
    analysis = {}
    
    for url in consistent_urls:
        scores = [result[url] for result in results]
        
        if len(scores) > 1:
            analysis[url] = {
                "mean": mean(scores),
                "stdev": stdev(scores) if len(scores) > 1 else 0.0,
                "min": min(scores),
                "max": max(scores),
                "range": max(scores) - min(scores),
                "scores": scores
            }
        else:
            analysis[url] = {
                "mean": scores[0],
                "stdev": 0.0,
                "min": scores[0], 
                "max": scores[0],
                "range": 0.0,
                "scores": scores
            }
    
    return analysis


def generate_consistency_report(analysis: Dict[str, Dict[str, float]], num_runs: int) -> str:
    """Generate human-readable consistency report."""
    
    report = [
        "# Clipper Consistency Analysis Report",
        f"**Runs:** {num_runs}",
        f"**URLs Tested:** {len(analysis)}",
        ""
    ]
    
    # Calculate overall statistics
    all_stdevs = [stats["stdev"] for stats in analysis.values()]
    all_ranges = [stats["range"] for stats in analysis.values()]
    
    avg_stdev = mean(all_stdevs) if all_stdevs else 0.0
    max_stdev = max(all_stdevs) if all_stdevs else 0.0
    avg_range = mean(all_ranges) if all_ranges else 0.0
    max_range = max(all_ranges) if all_ranges else 0.0
    
    report.extend([
        "## 📊 Overall Consistency",
        f"- **Average Standard Deviation:** {avg_stdev:.2f} points",
        f"- **Maximum Standard Deviation:** {max_stdev:.2f} points", 
        f"- **Average Score Range:** {avg_range:.2f} points",
        f"- **Maximum Score Range:** {max_range:.2f} points",
        ""
    ])
    
    # Flag inconsistent URLs (high variance)
    inconsistent = [(url, stats) for url, stats in analysis.items() 
                   if stats["stdev"] > 5.0 or stats["range"] > 10.0]
    
    if inconsistent:
        report.extend([
            "## ⚠️ Inconsistent Results (stdev > 5.0 or range > 10.0)",
            ""
        ])
        
        inconsistent.sort(key=lambda x: x[1]["stdev"], reverse=True)
        
        for url, stats in inconsistent:
            report.extend([
                f"### {url}",
                f"- **Mean:** {stats['mean']:.1f}",
                f"- **Standard Deviation:** {stats['stdev']:.2f}",
                f"- **Range:** {stats['min']:.1f} - {stats['max']:.1f}",
                f"- **Individual Scores:** {[f'{s:.1f}' for s in stats['scores']]}",
                ""
            ])
    else:
        report.extend([
            "## ✅ All Results Consistent",
            "No URLs showed high variance (stdev > 5.0 or range > 10.0)",
            ""
        ])
    
    # Summary by consistency level
    highly_consistent = sum(1 for stats in analysis.values() if stats["stdev"] <= 1.0)
    moderately_consistent = sum(1 for stats in analysis.values() if 1.0 < stats["stdev"] <= 3.0)
    somewhat_consistent = sum(1 for stats in analysis.values() if 3.0 < stats["stdev"] <= 5.0)
    inconsistent_count = len(inconsistent)
    
    report.extend([
        "## 📈 Consistency Distribution",
        f"- **Highly Consistent** (stdev ≤ 1.0): {highly_consistent} URLs",
        f"- **Moderately Consistent** (1.0 < stdev ≤ 3.0): {moderately_consistent} URLs", 
        f"- **Somewhat Consistent** (3.0 < stdev ≤ 5.0): {somewhat_consistent} URLs",
        f"- **Inconsistent** (stdev > 5.0): {inconsistent_count} URLs",
        ""
    ])
    
    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="Test Clipper consistency across multiple runs")
    parser.add_argument("urls_file", help="File containing URLs to test")
    parser.add_argument("--runs", "-r", type=int, default=3, 
                       help="Number of evaluation runs (default: 3)")
    parser.add_argument("--output", "-o", help="Save consistency report to file")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Show detailed progress")
    
    args = parser.parse_args()
    
    if not Path(args.urls_file).exists():
        print(f"❌ URLs file not found: {args.urls_file}")
        return 1
    
    print(f"🔄 Running {args.runs} consistency tests...")
    
    results = []
    
    for run_id in range(1, args.runs + 1):
        if args.verbose:
            print(f"  Run {run_id}/{args.runs}...")
        else:
            print(f"  Run {run_id}/{args.runs}", end="", flush=True)
        
        result = run_clipper_evaluation(args.urls_file, run_id, quiet=not args.verbose)
        
        if result:
            results.append(result)
            if not args.verbose:
                print(" ✅")
        else:
            if not args.verbose:
                print(" ❌")
    
    if not results:
        print("❌ No successful evaluation runs")
        return 1
    
    print(f"\n📊 Analyzing consistency across {len(results)} successful runs...")
    
    # Analyze consistency
    analysis = analyze_consistency(results)
    
    if not analysis:
        print("❌ No common URLs across runs")
        return 1
    
    # Generate report
    report = generate_consistency_report(analysis, len(results))
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"📄 Consistency report saved to {args.output}")
    
    print(report)
    
    # Determine if consistency is acceptable
    all_stdevs = [stats["stdev"] for stats in analysis.values()]
    max_stdev = max(all_stdevs) if all_stdevs else 0.0
    
    if max_stdev > 10.0:
        print("❌ FAIL: High variance detected (max stdev > 10.0)")
        return 1
    elif max_stdev > 5.0:
        print("⚠️  WARNING: Moderate variance detected (max stdev > 5.0)")
        return 0
    else:
        print(f"✅ PASS: Good consistency (max stdev = {max_stdev:.2f})")
        return 0


if __name__ == "__main__":
    exit(main())