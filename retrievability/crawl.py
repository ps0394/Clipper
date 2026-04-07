"""URL crawling and HTML snapshot capture."""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import requests
from urllib.parse import urlparse

from .schemas import CrawlResult


def crawl_urls(urls_file: str, output_dir: str) -> None:
    """Crawl URLs from file and save HTML snapshots.
    
    Args:
        urls_file: Path to file containing URLs (one per line)
        output_dir: Directory to save HTML snapshots
    """
    urls_path = Path(urls_file)
    if not urls_path.exists():
        raise FileNotFoundError(f"URLs file not found: {urls_file}")
        
    # Read URLs from file
    urls = []
    with open(urls_path, 'r', encoding='utf-8') as f:
        for line in f:
            url = line.strip()
            if url and not url.startswith('#'):  # Skip empty lines and comments
                urls.append(url)
    
    if not urls:
        raise ValueError(f"No valid URLs found in {urls_file}")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    for url in urls:
        print(f"Crawling: {url}")
        result = _crawl_single_url(url, output_path)
        results.append(result)
    
    # Save crawl results JSON
    crawl_results_file = output_path / "crawl_results.json"
    with open(crawl_results_file, 'w', encoding='utf-8') as f:
        json.dump([result.to_dict() for result in results], f, indent=2)
    
    print(f"Crawled {len(results)} URLs, results saved to {crawl_results_file}")


def _crawl_single_url(url: str, output_dir: Path) -> CrawlResult:
    """Crawl a single URL and capture HTML snapshot.
    
    Args:
        url: URL to crawl
        output_dir: Directory to save HTML snapshot
        
    Returns:
        CrawlResult with capture details
    """
    timestamp = datetime.now().isoformat()
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Retrievability-Eval/1.0 (Documentation Analysis Tool)'
    })
    
    try:
        # Perform HTTP request with redirects
        response = session.get(url, timeout=30, allow_redirects=True)
        
        # Generate unique filename based on URL hash  
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:12]
        html_filename = f"{url_hash}.html"
        html_path = output_dir / html_filename
        
        # Save raw HTML
        with open(html_path, 'w', encoding='utf-8', errors='replace') as f:
            f.write(response.text)
        
        # Extract headers as simple dict (convert case-insensitive headers)
        headers = dict(response.headers)
        
        return CrawlResult(
            url=url,
            timestamp=timestamp, 
            status=response.status_code,
            headers=headers,
            html_path=str(html_path.name)  # Relative to snapshots dir
        )
        
    except requests.RequestException as e:
        # Handle network/HTTP errors - create result with error status
        print(f"Error crawling {url}: {e}")
        
        return CrawlResult(
            url=url,
            timestamp=timestamp,
            status=0,  # Indicates request failure
            headers={'error': str(e)},
            html_path=""  # No HTML saved for failed requests
        )