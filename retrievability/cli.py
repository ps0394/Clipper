"""CLI entrypoint for retrievability evaluation system."""

import argparse
import sys
import tempfile
import os
from pathlib import Path
from typing import List

from .crawl import crawl_urls
from .parse import parse_snapshots  
from .score import score_parse_results
from .report import generate_report


def _create_urls_file(args) -> str:
    """Create a temporary URLs file from various input sources."""
    if hasattr(args, 'urls_file') and args.urls_file:
        return args.urls_file
    
    # Create temporary file for URLs
    temp_fd, temp_path = tempfile.mkstemp(suffix='.txt', prefix='urls_')
    
    try:
        with os.fdopen(temp_fd, 'w') as f:
            if hasattr(args, 'urls') and args.urls:
                # URLs from command line
                for url in args.urls:
                    f.write(f"{url.strip()}\n")
            elif hasattr(args, 'stdin') and args.stdin:
                # URLs from stdin
                for line in sys.stdin:
                    url = line.strip()
                    if url:
                        f.write(f"{url}\n")
        
        return temp_path
    except:
        os.unlink(temp_path)
        raise


def _cleanup_temp_file(file_path: str, original_file: str = None):
    """Remove temporary file if it was created."""
    if file_path != original_file and file_path.startswith(tempfile.gettempdir()):
        try:
            os.unlink(file_path)
        except:
            pass  # Ignore cleanup errors


def _print_summary(score_file: str, quiet: bool = False):
    """Print evaluation summary from score file."""
    import json
    
    try:
        with open(score_file) as f:
            scores = json.load(f)
        
        total = len(scores)
        if total == 0:
            print("No URLs evaluated.")
            return
            
        avg_score = sum(s['parseability_score'] for s in scores) / total
        clean = sum(1 for s in scores if s['failure_mode'] == 'clean')
        
        if not quiet:
            print(f"\n📊 Evaluation Results:")
            print(f"├─ Total URLs: {total}")
            print(f"├─ Average Score: {avg_score:.1f}/100")
            print(f"└─ Agent-Ready: {clean}/{total} ({clean/total*100:.1f}%)")
            
            print(f"\n📋 Individual Results:")
            for score in scores:
                url = score.get('url', 'Unknown URL')
                score_val = score['parseability_score']
                mode = score['failure_mode']
                emoji = '✅' if mode == 'clean' else '⚠️' if score_val >= 60 else '❌'
                print(f"  {emoji} {score_val:3.0f}/100 - {url}")
        else:
            print(f"{avg_score:.1f}/100 average, {clean}/{total} clean")
            
    except Exception as e:
        print(f"Error reading results: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='retrievability',
        description='Evaluate documentation page retrievability'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Crawl command
    crawl_parser = subparsers.add_parser('crawl', help='Fetch URLs and capture HTML snapshots')
    crawl_group = crawl_parser.add_mutually_exclusive_group(required=True)
    crawl_group.add_argument('urls_file', nargs='?', help='Path to file containing URLs (one per line)')
    crawl_group.add_argument('--urls', nargs='+', help='URLs to crawl directly (space-separated)')
    crawl_group.add_argument('--stdin', action='store_true', help='Read URLs from stdin (one per line)')
    crawl_parser.add_argument('--out', required=True, help='Output directory for HTML snapshots')
    
    # Parse command  
    parse_parser = subparsers.add_parser('parse', help='Extract parseability signals from HTML snapshots')
    parse_parser.add_argument('snapshots_dir', help='Directory containing HTML snapshots')
    parse_parser.add_argument('--out', required=True, help='Output JSON file for parse results')
    
    # Score command
    score_parser = subparsers.add_parser('score', help='Score parse results and classify failure modes')
    score_parser.add_argument('parse_file', help='JSON file with parse results')
    score_parser.add_argument('--out', required=True, help='Output JSON file for score results')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate human-readable markdown report')
    report_parser.add_argument('score_file', help='JSON file with score results')
    report_parser.add_argument('--md', required=True, help='Output markdown file for report')
    
    # Express command - full pipeline
    express_parser = subparsers.add_parser('express', help='Run full evaluation pipeline on URLs')
    express_group = express_parser.add_mutually_exclusive_group(required=True)
    express_group.add_argument('urls_file', nargs='?', help='Path to file containing URLs (one per line)')
    express_group.add_argument('--urls', nargs='+', help='URLs to evaluate directly (space-separated)')
    express_group.add_argument('--stdin', action='store_true', help='Read URLs from stdin (one per line)')
    express_parser.add_argument('--out', default='./evaluation', help='Output directory for all results (default: ./evaluation)')
    express_parser.add_argument('--name', default='report', help='Base name for output files (default: report)')
    express_parser.add_argument('--quiet', '-q', action='store_true', help='Only output final summary')
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'crawl':
            urls_file = _create_urls_file(args)
            try:
                crawl_urls(urls_file, args.out)
            finally:
                _cleanup_temp_file(urls_file, getattr(args, 'urls_file', None))
            
        elif args.command == 'parse':
            parse_snapshots(args.snapshots_dir, args.out)
            
        elif args.command == 'score':
            score_parse_results(args.parse_file, args.out)
            
        elif args.command == 'report':
            generate_report(args.score_file, args.md)
            
        elif args.command == 'express':
            # Full pipeline execution
            urls_file = _create_urls_file(args)
            
            try:
                # Setup output paths
                out_dir = Path(args.out)
                out_dir.mkdir(parents=True, exist_ok=True)
                
                snapshots_dir = out_dir / 'snapshots'
                parse_file = out_dir / f'{args.name}_parse.json'
                score_file = out_dir / f'{args.name}_scores.json' 
                report_file = out_dir / f'{args.name}.md'
                
                if not args.quiet:
                    print(f"🔄 Running evaluation pipeline...")
                    print(f"├─ Output directory: {out_dir}")
                    print(f"└─ Report files: {args.name}_*")
                
                # Run pipeline
                if not args.quiet:
                    print(f"\n1️⃣ Crawling URLs...")
                crawl_urls(urls_file, str(snapshots_dir))
                
                if not args.quiet:
                    print(f"2️⃣ Parsing content...")
                parse_snapshots(str(snapshots_dir), str(parse_file))
                
                if not args.quiet:
                    print(f"3️⃣ Scoring results...")
                score_parse_results(str(parse_file), str(score_file))
                
                if not args.quiet:
                    print(f"4️⃣ Generating report...")
                generate_report(str(score_file), str(report_file))
                
                # Show summary
                _print_summary(str(score_file), args.quiet)
                
                if not args.quiet:
                    print(f"\n📄 Full report saved to: {report_file}")
                
            finally:
                _cleanup_temp_file(urls_file, getattr(args, 'urls_file', None))
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()