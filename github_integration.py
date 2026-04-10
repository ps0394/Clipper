#!/usr/bin/env python3
"""
GitHub Integration Helper for Retrievability Evaluation

This script demonstrates how to integrate the retrievability evaluation system
with GitHub APIs, custom workflows, and external tools.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile
import argparse


class GitHubDocsEvaluator:
    """Helper class for GitHub-integrated documentation evaluation."""
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        
    def run_evaluation_pipeline(self, urls_file: str, output_dir: str) -> Dict:
        """Run the complete YARA evaluation pipeline.
        
        Args:
            urls_file: Path to file containing URLs to evaluate
            output_dir: Directory to save results
            
        Returns:
            Dictionary with evaluation results and metrics
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Step 1: Crawl
            print("📥 Step 1/4: Crawling URLs...")
            self._run_cli_command([
                'crawl', urls_file, '--out', str(output_path / 'snapshots')
            ])
            
            # Step 2: Parse
            print("🧩 Step 2/4: Parsing HTML...")
            self._run_cli_command([
                'parse', str(output_path / 'snapshots'), 
                '--out', str(output_path / 'parse.json')
            ])
            
            # Step 3: Score
            print("📊 Step 3/4: Scoring results...")
            self._run_cli_command([
                'score', str(output_path / 'parse.json'),
                '--out', str(output_path / 'scores.json')
            ])
            
            # Step 4: Report
            print("📄 Step 4/4: Generating report...")
            self._run_cli_command([
                'report', str(output_path / 'scores.json'),
                '--md', str(output_path / 'report.md')
            ])
            
            # Load and return results
            with open(output_path / 'scores.json') as f:
                scores = json.load(f)
                
            metrics = self._calculate_metrics(scores)
            
            return {
                'success': True,
                'scores': scores,
                'metrics': metrics,
                'files': {
                    'scores': str(output_path / 'scores.json'),
                    'report': str(output_path / 'report.md'),
                    'parse': str(output_path / 'parse.json')
                }
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': f"CLI command failed: {e}",
                'returncode': e.returncode
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Evaluation failed: {e}"
            }
    
    def _run_cli_command(self, args: List[str]) -> None:
        """Run a retrievability CLI command."""
        cmd = [sys.executable, '-m', 'retrievability.cli'] + args
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # Print output for debugging
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    
    def _calculate_metrics(self, scores: List[Dict]) -> Dict:
        """Calculate summary metrics from scores."""
        if not scores:
            return {}
            
        total_pages = len(scores)
        avg_score = sum(s['parseability_score'] for s in scores) / total_pages
        
        clean_count = sum(1 for s in scores if s['failure_mode'] == 'clean')
        structure_missing = sum(1 for s in scores if s['failure_mode'] == 'structure-missing')
        extraction_noisy = sum(1 for s in scores if s['failure_mode'] == 'extraction-noisy')
        
        return {
            'total_pages': total_pages,
            'average_score': round(avg_score, 1),
            'clean_count': clean_count,
            'clean_percentage': round((clean_count / total_pages) * 100, 1),
            'structure_missing': structure_missing,
            'extraction_noisy': extraction_noisy
        }
    
    def check_quality_gates(self, metrics: Dict, min_score: float = 70, 
                          min_clean_percentage: float = 60) -> Tuple[bool, List[str]]:
        """Check if metrics pass quality gates.
        
        Returns:
            Tuple of (passed, list of failure reasons)
        """
        failures = []
        
        if metrics['average_score'] < min_score:
            failures.append(f"Average score {metrics['average_score']} below {min_score}")
            
        if metrics['clean_percentage'] < min_clean_percentage:
            failures.append(f"Clean percentage {metrics['clean_percentage']}% below {min_clean_percentage}%")
        
        return len(failures) == 0, failures
    
    def create_github_comment_summary(self, metrics: Dict, quality_passed: bool,
                                    quality_failures: List[str]) -> str:
        """Generate a GitHub-formatted comment summary."""
        
        status_emoji = "✅" if quality_passed else "❌"
        
        summary = f"""## {status_emoji} Documentation Quality Report

**Overall Metrics:**
- 📈 **Average Score**: {metrics['average_score']}/100
- ✅ **Clean Pages**: {metrics['clean_count']}/{metrics['total_pages']} ({metrics['clean_percentage']}%)
- 🔧 **Structure Issues**: {metrics['structure_missing']} pages
- ⚠️ **Extraction Issues**: {metrics['extraction_noisy']} pages

**Quality Gates:** {'✅ PASSED' if quality_passed else '❌ FAILED'}"""

        if quality_failures:
            summary += "\n\n**Issues:**"
            for failure in quality_failures:
                summary += f"\n- ❌ {failure}"
        
        return summary


def main():
    """CLI entry point for GitHub integration helper."""
    parser = argparse.ArgumentParser(
        description="GitHub integration helper for YARA (Yet Another Retrieval Analyzer)"
    )
    parser.add_argument('command', choices=['evaluate', 'check-gates'], 
                       help='Command to run')
    parser.add_argument('--urls-file', required=True,
                       help='File containing URLs to evaluate')
    parser.add_argument('--output-dir', default='github-eval-results',
                       help='Output directory for results')
    parser.add_argument('--min-score', type=float, default=70,
                       help='Minimum average score threshold')
    parser.add_argument('--min-clean-percentage', type=float, default=60,
                       help='Minimum clean pages percentage threshold')
    parser.add_argument('--github-output', 
                       help='Path to GitHub Actions output file')
    
    args = parser.parse_args()
    
    evaluator = GitHubDocsEvaluator()
    
    if args.command == 'evaluate':
        print("🚀 Running documentation evaluation for GitHub integration...")
        
        result = evaluator.run_evaluation_pipeline(args.urls_file, args.output_dir)
        
        if not result['success']:
            print(f"❌ Evaluation failed: {result['error']}")
            sys.exit(1)
            
        metrics = result['metrics']
        quality_passed, quality_failures = evaluator.check_quality_gates(
            metrics, args.min_score, args.min_clean_percentage
        )
        
        print(f"\n📊 Results:")
        print(f"   Average Score: {metrics['average_score']}/100")
        print(f"   Clean Pages: {metrics['clean_count']}/{metrics['total_pages']} ({metrics['clean_percentage']}%)")
        print(f"   Quality Gates: {'✅ PASSED' if quality_passed else '❌ FAILED'}")
        
        if quality_failures:
            print(f"\n❌ Quality Gate Failures:")
            for failure in quality_failures:
                print(f"   • {failure}")
        
        # Set GitHub Actions outputs if requested
        if args.github_output and os.path.exists(os.path.dirname(args.github_output)):
            with open(args.github_output, 'a') as f:
                f.write(f"avg_score={metrics['average_score']}\n")
                f.write(f"clean_count={metrics['clean_count']}\n")
                f.write(f"clean_percentage={metrics['clean_percentage']}\n")
                f.write(f"total_pages={metrics['total_pages']}\n")
                f.write(f"quality_passed={str(quality_passed).lower()}\n")
        
        # Generate GitHub comment
        comment = evaluator.create_github_comment_summary(
            metrics, quality_passed, quality_failures
        )
        
        comment_file = Path(args.output_dir) / 'github-comment.md'
        with open(comment_file, 'w') as f:
            f.write(comment)
        
        print(f"\n📝 GitHub comment generated: {comment_file}")
        
        if not quality_passed:
            sys.exit(1)
            
    elif args.command == 'check-gates':
        # Load existing results and check gates
        scores_file = Path(args.output_dir) / 'scores.json'
        if not scores_file.exists():
            print(f"❌ Scores file not found: {scores_file}")
            sys.exit(1)
            
        with open(scores_file) as f:
            scores = json.load(f)
            
        metrics = evaluator._calculate_metrics(scores)
        quality_passed, quality_failures = evaluator.check_quality_gates(
            metrics, args.min_score, args.min_clean_percentage
        )
        
        print(f"Quality Gates: {'✅ PASSED' if quality_passed else '❌ FAILED'}")
        
        if not quality_passed:
            for failure in quality_failures:
                print(f"   • {failure}")
            sys.exit(1)


if __name__ == '__main__':
    main()