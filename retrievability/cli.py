"""CLI entrypoint for retrievability evaluation system."""

import argparse
import sys
from pathlib import Path
from typing import List

from .crawl import crawl_urls
from .parse import parse_snapshots  
from .score import score_parse_results
from .report import generate_report


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='retrievability',
        description='Evaluate documentation page retrievability'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Crawl command
    crawl_parser = subparsers.add_parser('crawl', help='Fetch URLs and capture HTML snapshots')
    crawl_parser.add_argument('urls_file', help='Path to file containing URLs (one per line)')
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
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'crawl':
            crawl_urls(args.urls_file, args.out)
            
        elif args.command == 'parse':
            parse_snapshots(args.snapshots_dir, args.out)
            
        elif args.command == 'score':
            score_parse_results(args.parse_file, args.out)
            
        elif args.command == 'report':
            generate_report(args.score_file, args.md)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()