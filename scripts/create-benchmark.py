#!/usr/bin/env python3
"""Create curated benchmark URL sets for Clipper validation."""

import argparse
from pathlib import Path

# Curated benchmark URL collections
BENCHMARK_SETS = {
    "champions": [
        "https://docs.github.com/en",
        "https://learn.microsoft.com/en-us/azure/",
        "https://developer.mozilla.org/en-US/docs/Web/HTML",
        "https://docs.python.org/3/tutorial/",
        "https://kubernetes.io/docs/concepts/overview/what-is-kubernetes/",
        "https://reactjs.org/docs/getting-started.html",
    ],
    
    "problematic": [
        "https://stackoverflow.com/questions/tagged/azure",
        "https://reddit.com/r/programming", 
        "https://techcrunch.com",
        "https://buzzfeed.com",
        "https://old-forum-example.com",
    ],
    
    "decent": [
        "https://en.wikipedia.org/wiki/Cloud_computing",
        "https://cloud.google.com/functions/docs/concepts/overview",
        "https://aws.amazon.com/s3/getting-started/",
        "https://medium.com/@tech/programming-article",
        "https://blog.golang.org/go1.15",
    ],
    
    "edge_cases": [
        "https://news.ycombinator.com",
        "https://single-page-app.example.com",
        "https://pdf-like-document.example.com",
        "https://heavy-javascript-site.example.com",
    ],
    
    "mixed": [
        # Mix of all categories for comprehensive testing
        "https://docs.github.com/en",
        "https://stackoverflow.com/questions/tagged/python",
        "https://en.wikipedia.org/wiki/Machine_learning", 
        "https://learn.microsoft.com/en-us/dotnet/",
        "https://news.ycombinator.com",
        "https://developer.mozilla.org/en-US/docs/Web/CSS",
        "https://aws.amazon.com/documentation/",
        "https://reddit.com/r/webdev",
    ]
}


def create_benchmark_set(set_name: str, output_file: str):
    """Create a benchmark URL set file."""
    
    if set_name not in BENCHMARK_SETS:
        available = ", ".join(BENCHMARK_SETS.keys())
        raise ValueError(f"Unknown benchmark set '{set_name}'. Available: {available}")
    
    urls = BENCHMARK_SETS[set_name]
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        for url in urls:
            f.write(f"{url}\n")
    
    print(f"📝 Created benchmark set '{set_name}' with {len(urls)} URLs")
    print(f"   Saved to: {output_path}")
    print(f"   Run: python -m retrievability.cli express {output_file} --out benchmark-{set_name}")


def list_benchmark_sets():
    """List available benchmark sets with descriptions."""
    
    descriptions = {
        "champions": "High-quality documentation sites (should score 80-100)",
        "problematic": "Poor structure/high noise sites (should score 20-50)", 
        "decent": "Average sites with some issues (should score 50-80)",
        "edge_cases": "Challenging cases (variable scores)",
        "mixed": "Comprehensive mix of all categories",
    }
    
    print("📋 Available Benchmark Sets:")
    print()
    
    for set_name, urls in BENCHMARK_SETS.items():
        desc = descriptions.get(set_name, "No description")
        print(f"**{set_name}** ({len(urls)} URLs)")
        print(f"  {desc}")
        print(f"  Examples: {', '.join(urls[:2])}...")
        print()


def validate_urls():
    """Quick validation that benchmark URLs are accessible."""
    import requests
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    def check_url(url):
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            return url, response.status_code, None
        except Exception as e:
            return url, None, str(e)
    
    all_urls = []
    for urls in BENCHMARK_SETS.values():
        all_urls.extend(urls)
    
    unique_urls = list(set(all_urls))
    print(f"🔍 Validating {len(unique_urls)} unique benchmark URLs...")
    
    results = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_url, url): url for url in unique_urls}
        
        for future in as_completed(futures):
            url, status_code, error = future.result()
            
            if error:
                results[url] = f"❌ Error: {error}"
            elif status_code and 200 <= status_code < 400:
                results[url] = f"✅ {status_code}"
            else:
                results[url] = f"⚠️  {status_code}"
    
    # Print results
    print("\n📊 URL Validation Results:")
    for url, result in sorted(results.items()):
        print(f"  {result} - {url}")
    
    # Summary
    ok_count = sum(1 for r in results.values() if r.startswith("✅"))
    print(f"\n✅ {ok_count}/{len(unique_urls)} URLs accessible ({ok_count/len(unique_urls)*100:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Create curated benchmark URL sets for Clipper validation")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Create benchmark set
    create_parser = subparsers.add_parser("create", help="Create a benchmark URL set")
    create_parser.add_argument("set_name", help="Name of benchmark set to create")
    create_parser.add_argument("--output", "-o", required=True, help="Output file for URL list")
    
    # List available sets
    list_parser = subparsers.add_parser("list", help="List available benchmark sets")
    
    # Validate URLs
    validate_parser = subparsers.add_parser("validate", help="Check that benchmark URLs are accessible")
    
    args = parser.parse_args()
    
    if args.command == "create":
        create_benchmark_set(args.set_name, args.output)
    elif args.command == "list":
        list_benchmark_sets()
    elif args.command == "validate":
        validate_urls()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()