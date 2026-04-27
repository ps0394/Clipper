"""CLI entrypoint for retrievability evaluation system."""

import argparse
import sys
import tempfile
import os
from pathlib import Path
from typing import List

# Lazy imports - load modules only when needed to avoid hanging on startup
# from .crawl import crawl_urls, crawl_with_content_negotiation
# from .parse import parse_snapshots  
# from .score import score_parse_results
# from .report import generate_report


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
    from pathlib import Path
    
    try:
        with open(score_file) as f:
            scores = json.load(f)
        
        # Try to find the corresponding crawl_results.json file
        # Check both same directory and snapshots subdirectory
        score_path = Path(score_file)
        crawl_file = score_path.parent / "crawl_results.json"
        snapshots_crawl_file = score_path.parent / "snapshots" / "crawl_results.json"
        
        urls = []
        
        # Try snapshots subdirectory first, then same directory
        if snapshots_crawl_file.exists():
            try:
                with open(snapshots_crawl_file) as f:
                    crawl_results = json.load(f)
                urls = [result['url'] for result in crawl_results]
            except:
                pass  # Fallback to trying same directory
        elif crawl_file.exists():
            try:
                with open(crawl_file) as f:
                    crawl_results = json.load(f)
                urls = [result['url'] for result in crawl_results]
            except:
                pass  # Fallback to unknown URLs
        
        total = len(scores)
        if total == 0:
            print("No URLs evaluated.")
            return
            
        avg_score = sum(s['parseability_score'] for s in scores) / total
        # Count ready URLs (success in hybrid mode)
        clean = sum(1 for s in scores if s['failure_mode'] in ['clean', 'success'])
        
        if not quiet:
            print(f"\n[RESULTS] Clipper Evaluation Results:")
            print(f"|- Total URLs: {total}")
            print(f"|- Average Score: {avg_score:.1f}/100")
            print(f"+- Agent-Ready: {clean}/{total} ({clean/total*100:.1f}%)")
            
            print(f"\n[RESULTS] Individual Results:")
            for i, score in enumerate(scores):
                # Get URL from crawl results if available, otherwise use fallback
                if i < len(urls):
                    url = urls[i]
                else:
                    url = score.get('url', 'Unknown URL')
                
                score_val = score['parseability_score']
                mode = score['failure_mode']
                if score.get('partial_evaluation'):
                    emoji = '[PARTIAL]'
                else:
                    emoji = '[PASS]' if mode == 'clean' else '[WARN]' if score_val >= 60 else '[FAIL]'
                failed = score.get('failed_pillars') or []
                suffix = f"  (failed: {', '.join(failed)})" if failed else ''
                print(f"  {emoji} {score_val:3.0f}/100 - {url}{suffix}")
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
    
    # Content Negotiation command
    negotiate_parser = subparsers.add_parser('negotiate', help='Test content negotiation - check for markdown, JSON, etc.')
    negotiate_group = negotiate_parser.add_mutually_exclusive_group(required=True)
    negotiate_group.add_argument('urls_file', nargs='?', help='Path to file containing URLs (one per line)')
    negotiate_group.add_argument('--urls', nargs='+', help='URLs to test directly (space-separated)')
    negotiate_group.add_argument('--stdin', action='store_true', help='Read URLs from stdin (one per line)')
    negotiate_parser.add_argument('--out', required=True, help='Output directory for content negotiation results')
    
    # Parse command  
    parse_parser = subparsers.add_parser('parse', help='Extract parseability signals from HTML snapshots')
    parse_parser.add_argument('snapshots_dir', help='Directory containing HTML snapshots')
    parse_parser.add_argument('--out', required=True, help='Output JSON file for parse results')
    
    # Score command
    score_parser = subparsers.add_parser('score', help='Score parse results using Clipper standards-based methodology')
    score_parser.add_argument('parse_file', help='JSON file with parse results')
    score_parser.add_argument('--out', required=True, help='Output JSON file for score results')
    score_parser.add_argument('--api-key', help='Deprecated: Clipper is API-free and uses industry standards')
    score_parser.add_argument('--performance', action='store_true', help='Enable performance optimization mode (2-3x faster, default: enabled)')
    score_parser.add_argument('--standard', action='store_true', help='Use standard evaluation mode (for comparison/debugging)')
    score_parser.add_argument('--benchmark', action='store_true', help='Run performance comparison benchmark')
    score_parser.add_argument(
        '--render-mode',
        choices=['raw', 'rendered', 'both'],
        default='rendered',
        help="Rendering mode — see 'express --help' for details.",
    )
    
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
    express_parser.add_argument('--api-key', help='Deprecated: Clipper is API-free and uses industry standards')
    express_parser.add_argument('--performance', action='store_true', help='Enable performance optimization mode (2-3x faster, DEFAULT)')
    express_parser.add_argument('--standard', action='store_true', help='Use standard evaluation mode (slower, for debugging)')
    express_parser.add_argument('--benchmark', action='store_true', help='Run performance comparison after evaluation')
    express_parser.add_argument(
        '--render-mode',
        choices=['raw', 'rendered', 'both'],
        default='rendered',
        help=(
            "Which rendering mode(s) to evaluate. 'rendered' (default) uses "
            "the full browser/axe pass for DOM navigability; 'raw' forces "
            "static-only analysis with no browser call at all, modeling "
            "agents that do not execute JavaScript; 'both' emits two "
            "ScoreResults per URL plus a parseability delta in the report."
        ),
    )

    # History command - trend view across prior evaluations (Phase 4.2)
    history_parser = subparsers.add_parser(
        'history',
        help='Show how a URL has scored across prior evaluations',
    )
    history_parser.add_argument('url', help='URL to look up')
    history_parser.add_argument(
        '--root',
        default='evaluation',
        help='Directory to walk for *_scores.json files (default: evaluation)',
    )
    history_parser.add_argument(
        '--json',
        action='store_true',
        help='Emit JSON rather than the table view',
    )

    # Phase 5 command group - LLM ground-truth validation (scaffolding)
    phase5_parser = subparsers.add_parser(
        'phase5',
        help='Phase 5 LLM ground-truth validation (see docs/phase-5-design.md)',
    )
    phase5_sub = phase5_parser.add_subparsers(dest='phase5_command')
    phase5_status_parser = phase5_sub.add_parser(
        'status',
        help='Show Phase 5 scaffolding status and what still needs wiring',
    )
    phase5_status_parser.add_argument(
        '--check',
        action='store_true',
        help='Ping each configured Foundry deployment to verify credentials + connectivity',
    )
    phase5_pilot_parser = phase5_sub.add_parser(
        'pilot',
        help='Run the N=5 pilot: fetch -> generate -> review -> score -> grade',
    )
    phase5_pilot_parser.add_argument(
        'urls_file',
        help='Text file of URLs to pilot (one per line; optional tab-separated profile)',
    )
    phase5_pilot_parser.add_argument(
        '--out',
        required=True,
        help='Output directory for pilot results',
    )
    phase5_pilot_parser.add_argument(
        '--review',
        action='store_true',
        help='Interactively review generated Q/A pairs (default: auto-accept)',
    )
    phase5_pilot_parser.add_argument(
        '--reviewer-id',
        default='auto',
        help='Reviewer identifier recorded in review.json',
    )
    phase5_pilot_parser.add_argument(
        '--secondary-scorer',
        action='store_true',
        help='Also run the secondary scorer (Llama) for cross-LLM agreement check',
    )
    phase5_pilot_parser.add_argument(
        '--grader',
        choices=['substring', 'llm'],
        default='llm',
        help='Grader: llm (Llama 3.3 as judge, semantically-tolerant; default) '
             'or substring (fast heuristic, false-negatives on paraphrase)',
    )
    phase5_pilot_parser.add_argument(
        '--generator-prompt',
        default='generator',
        help='Name of the generator prompt template under retrievability/phase5/prompts/ '
             '(default: generator). Use e.g. "generator-hard" to run with a harder-Q/A '
             'prompt without changing the baseline.',
    )

    phase5_rejudge_parser = phase5_sub.add_parser(
        'rejudge',
        help='Re-grade an existing pilot dir with the LLM judge (no re-fetch, no re-score)',
    )
    phase5_rejudge_parser.add_argument(
        'pilot_dir',
        help='Path to an existing pilot output directory (e.g. evaluation/phase5-results/pilot-001)',
    )
    phase5_rejudge_parser.add_argument(
        '--judge-id',
        default='primary',
        help='Tag for output files: grades.<judge_id>.judged.{rendered,}.json. '
             'Default "primary" preserves the original single-judge flow. '
             'Use distinct tags (e.g. "claude35", "geminiPro") for Phase 6 '
             'cross-judge regrading (F3.2).',
    )
    phase5_rejudge_parser.add_argument(
        '--judge-deployment-env',
        default='PHASE5_SCORER_SECONDARY_DEPLOYMENT',
        help='Name of the env var that holds the Foundry deployment name for '
             'this judge. Default PHASE5_SCORER_SECONDARY_DEPLOYMENT matches '
             'the pilot calibration flow. For Phase 6 F3.2, set a new var '
             '(e.g. PHASE5_JUDGE_CLAUDE35_DEPLOYMENT) in .env and pass it '
             'here. The referenced deployment still resolves through the '
             'same Foundry endpoint + API key in .env.',
    )

    phase5_kappa_parser = phase5_sub.add_parser(
        'kappa',
        help='Compute Cohen\'s kappa between hand-labels and judge-labels for the calibration gate',
    )
    phase5_kappa_parser.add_argument(
        'pilot_dir',
        help='Path to an existing pilot output directory',
    )

    phase5_regrade_md_parser = phase5_sub.add_parser(
        'regrade-markdown',
        help='F4.2 paired grading: fetch served markdown via the tri-fetcher '
             'and re-score each page against its existing qapairs.json',
    )
    phase5_regrade_md_parser.add_argument(
        'pilot_dir',
        help='Path to an existing pilot output directory (will read URLs from '
             'each page\'s summary.json; writes fetch.markdown.json, '
             'page.markdown.txt, scoring.primary.markdown.json, '
             'grades.primary.markdown.json, and (optionally) '
             'grades.primary.judged.markdown.json into each page dir, plus '
             'markdown-regrade-summary.json at the pilot root).',
    )
    phase5_regrade_md_parser.add_argument(
        '--no-judge',
        action='store_true',
        help='Skip LLM-judge grading (substring grading only). Use to keep '
             'costs down when a quick lift estimate is sufficient.',
    )

    phase5_regrade_int_parser = phase5_sub.add_parser(
        'regrade-intersection',
        help='F4.2 Track B paired grading: generate fresh Q/A from the '
             'rendered-vs-markdown content intersection and grade BOTH '
             'versions against them. Corrects the HTML-source bias of '
             'regrade-markdown.',
    )
    phase5_regrade_int_parser.add_argument(
        'pilot_dir',
        help='Path to an existing pilot output directory that already has '
             'page.rendered.txt and page.markdown.txt for each page (run '
             'regrade-markdown first to populate page.markdown.txt).',
    )
    phase5_regrade_int_parser.add_argument(
        '--no-judge',
        action='store_true',
        help='Skip LLM-judge grading (substring grading only).',
    )
    phase5_regrade_int_parser.add_argument(
        '--min-chars',
        type=int,
        default=1500,
        help='Minimum intersection char length to attempt Q/A generation '
             '(default 1500; matches MIN_DOCUMENT_CHARS).',
    )

    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'crawl':
            # Lazy import - load only when needed
            from .crawl import crawl_urls
            urls_file = _create_urls_file(args)
            try:
                crawl_urls(urls_file, args.out)
            finally:
                _cleanup_temp_file(urls_file, getattr(args, 'urls_file', None))
            
        elif args.command == 'negotiate':
            # Lazy import - load only when needed
            from .crawl import crawl_with_content_negotiation
            urls_file = _create_urls_file(args)
            try:
                crawl_with_content_negotiation(urls_file, args.out)
            finally:
                _cleanup_temp_file(urls_file, getattr(args, 'urls_file', None))
            
        elif args.command == 'parse':
            # Lazy import - load only when needed
            from .parse import parse_snapshots
            parse_snapshots(args.snapshots_dir, args.out)
            
        elif args.command == 'score':
            # Determine which scoring mode to use
            use_performance = not args.standard  # Default to performance mode unless --standard is specified
            
            if args.benchmark:
                # Run benchmark comparison
                from .performance_score import benchmark_performance_modes
                benchmark_performance_modes(args.parse_file)
                return
            
            if use_performance:
                # Use performance-optimized scoring
                from .performance_score import score_parse_results_fast
                api_key = getattr(args, 'api_key', None)
                score_parse_results_fast(
                    args.parse_file, args.out, api_key=api_key,
                    use_performance_mode=True,
                    render_mode=getattr(args, 'render_mode', 'rendered'),
                )
            else:
                # Use standard scoring for comparison/debugging
                from .score import score_parse_results
                api_key = getattr(args, 'api_key', None)
                score_parse_results(args.parse_file, args.out, api_key=api_key)
            
        elif args.command == 'report':
            # Lazy import - load only when needed
            from .report import generate_report
            generate_report(args.score_file, args.md)

        elif args.command == 'history':
            from .history import run_history
            sys.exit(run_history(args.url, root=args.root, as_json=args.json))

        elif args.command == 'phase5':
            from .phase5 import cli as phase5_cli
            sys.exit(phase5_cli.dispatch(args))

        elif args.command == 'express':
            # Determine scoring mode
            use_performance = not args.standard  # Default to performance mode
            
            # Lazy imports - load only when needed
            from .crawl import crawl_urls
            from .parse import parse_snapshots
            
            if use_performance:
                from .performance_score import score_parse_results_fast
            else:
                from .score import score_parse_results
                
            from .report import generate_report
            
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
                    mode_str = "Performance Mode" if use_performance else "Standard Mode"
                    print(f"🔄 Running evaluation pipeline ({mode_str})...")
                    print(f"|- Output directory: {out_dir}")
                    print(f"+- Report files: {args.name}_*")
                
                # Run pipeline
                if not args.quiet:
                    print(f"\n1️⃣ Crawling URLs...")
                crawl_urls(urls_file, str(snapshots_dir))
                
                if not args.quiet:
                    print(f"2️⃣ Parsing content...")
                parse_snapshots(str(snapshots_dir), str(parse_file))
                
                if not args.quiet:
                    performance_text = "Performance-Optimized" if use_performance else "Standard"
                    print(f"3️⃣ Scoring results (Clipper {performance_text})...")
                    
                api_key = getattr(args, 'api_key', None)
                
                if use_performance:
                    score_parse_results_fast(
                        str(parse_file), str(score_file), api_key=api_key,
                        use_performance_mode=True,
                        render_mode=getattr(args, 'render_mode', 'rendered'),
                    )
                else:
                    score_parse_results(str(parse_file), str(score_file), api_key=api_key)
                
                if not args.quiet:
                    print(f"4️⃣ Generating report...")
                generate_report(str(score_file), str(report_file))
                
                # Show summary
                _print_summary(str(score_file), args.quiet)
                
                if not args.quiet:
                    print(f"\n📄 Full report saved to: {report_file}")
                
                # Run benchmark if requested
                if args.benchmark:
                    if not args.quiet:
                        print(f"\n🏁 Running performance benchmark...")
                    from .performance_score import benchmark_performance_modes
                    benchmark_performance_modes(str(parse_file))
                
            finally:
                _cleanup_temp_file(urls_file, getattr(args, 'urls_file', None))
            
    except Exception as e:
        import traceback
        print(f"Error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()