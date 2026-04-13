"""URL crawling and HTML snapshot capture with redirect chain tracking."""

import json
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import requests
from urllib.parse import urlparse, urljoin

from .schemas import CrawlResult, FormatResponse, ContentNegotiationResult, RedirectStep


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
    """Crawl a single URL with redirect chain tracking.
    
    Args:
        url: URL to crawl
        output_dir: Directory to save HTML snapshot
        
    Returns:
        CrawlResult with capture details and redirect chain analysis
    """
    timestamp = datetime.now().isoformat()
    original_url = url
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Clipper-Eval/3.0 (Content Evaluation Tool with Redirect Analysis)'
    })
    
    # Track redirect chain manually
    redirect_chain = []
    total_start_time = time.time()
    redirect_start_time = total_start_time
    
    try:
        # Manual redirect handling for chain tracking
        current_url = url
        max_redirects = 10  # Prevent infinite loops
        redirect_count = 0
        
        while redirect_count < max_redirects:
            step_start_time = time.time()
            
            # Make request without following redirects
            response = session.get(current_url, timeout=30, allow_redirects=False)
            
            step_time_ms = (time.time() - step_start_time) * 1000
            
            # Check if this is a redirect
            if response.status_code in [301, 302, 303, 307, 308]:
                location = response.headers.get('Location')
                if not location:
                    break  # No location header, stop
                
                # Handle relative URLs
                if not location.startswith(('http://', 'https://')):
                    location = urljoin(current_url, location)
                
                # Record redirect step
                redirect_step = RedirectStep(
                    from_url=current_url,
                    to_url=location,
                    status_code=response.status_code,
                    redirect_time_ms=step_time_ms,
                    headers=dict(response.headers)
                )
                redirect_chain.append(redirect_step)
                
                current_url = location
                redirect_count += 1
                
                # Check for redirect loops
                visited_urls = [step.to_url for step in redirect_chain]
                if visited_urls.count(current_url) > 1:
                    break  # Redirect loop detected
                    
            else:
                # Final response (non-redirect)
                break
        
        # Get final response if we ended on a redirect
        if response.status_code in [301, 302, 303, 307, 308]:
            final_start_time = time.time()
            response = session.get(current_url, timeout=30, allow_redirects=False)
            final_response_time_ms = (time.time() - final_start_time) * 1000
        else:
            final_response_time_ms = step_time_ms
            
        total_redirect_time_ms = (time.time() - redirect_start_time) * 1000 - final_response_time_ms
        
        # Generate unique filename based on original URL hash  
        url_hash = hashlib.md5(original_url.encode('utf-8')).hexdigest()[:12]
        html_filename = f"{url_hash}.html"
        html_path = output_dir / html_filename
        
        # Save raw HTML from final response
        with open(html_path, 'w', encoding='utf-8', errors='replace') as f:
            f.write(response.text)
        
        # Extract headers as simple dict (convert case-insensitive headers)
        headers = dict(response.headers)
        
        return CrawlResult(
            url=original_url,
            timestamp=timestamp, 
            status=response.status_code,
            headers=headers,
            html_path=str(html_path.name),  # Relative to snapshots dir
            redirect_chain=redirect_chain,
            redirect_count=len(redirect_chain),
            total_redirect_time_ms=total_redirect_time_ms,
            final_response_time_ms=final_response_time_ms,
            final_url=current_url
        )
        
    except requests.RequestException as e:
        # Handle network/HTTP errors - create result with error status
        print(f"Error crawling {original_url}: {e}")
        
        return CrawlResult(
            url=original_url,
            timestamp=timestamp,
            status=0,  # Indicates request failure
            headers={'error': str(e)},
            html_path="",  # No HTML saved for failed requests
            redirect_chain=redirect_chain,  # Include any redirects that worked
            redirect_count=len(redirect_chain),
            total_redirect_time_ms=0.0,
            final_response_time_ms=0.0,
            final_url=original_url
        )


def crawl_with_content_negotiation(urls_file: str, output_dir: str) -> None:
    """Crawl URLs with content negotiation testing.
    
    Args:
        urls_file: Path to file containing URLs (one per line)
        output_dir: Directory to save content negotiation results
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
        print(f"Testing content negotiation for: {url}")
        result = _test_content_negotiation(url, output_path)
        results.append(result)
    
    # Save content negotiation results JSON
    negotiation_results_file = output_path / "content_negotiation_results.json"
    with open(negotiation_results_file, 'w', encoding='utf-8') as f:
        json.dump([result.to_dict() for result in results], f, indent=2)
    
    print(f"Tested {len(results)} URLs, results saved to {negotiation_results_file}")


def _test_content_negotiation(url: str, output_dir: Path) -> ContentNegotiationResult:
    """Test content negotiation for a single URL.
    
    Args:
        url: URL to test
        output_dir: Directory to save content files
        
    Returns:
        ContentNegotiationResult with format availability data
    """
    timestamp = datetime.now().isoformat()
    
    # Define Accept headers to test
    test_formats = [
        ('text/html', 'html'),  # Baseline (current behavior)
        ('text/markdown', 'md'),
        ('text/plain', 'txt'),  
        ('application/json', 'json'),
        ('application/xml', 'xml')
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Clipper-ContentEvaluation/1.0 (Agent-Friendly Content Evaluator)'
    })
    
    baseline_format = None
    alternative_formats = []
    
    # Generate unique filename base from URL hash
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:12]
    
    for accept_header, file_extension in test_formats:
        try:
            start_time = time.time()
            response = session.get(url, 
                                 headers={'Accept': accept_header},
                                 timeout=30, 
                                 allow_redirects=True)
            end_time = time.time()
            
            response_time_ms = int((end_time - start_time) * 1000)
            
            # Save content to file
            content_filename = f"{url_hash}_{file_extension}.{file_extension}"
            content_path = output_dir / content_filename
            
            with open(content_path, 'w', encoding='utf-8', errors='replace') as f:
                f.write(response.text)
            
            # Generate content hash for comparison
            content_hash = hashlib.md5(response.text.encode('utf-8')).hexdigest()
            
            format_response = FormatResponse(
                accept_header=accept_header,
                content_type=response.headers.get('content-type', ''),
                content_length=len(response.text),
                status_code=response.status_code,
                content_hash=content_hash,
                html_path=content_filename,
                response_time_ms=response_time_ms
            )
            
            if accept_header == 'text/html':
                baseline_format = format_response
            else:
                alternative_formats.append(format_response)
                
        except requests.RequestException as e:
            print(f"  Failed {accept_header}: {e}")
            # Create failed response record
            format_response = FormatResponse(
                accept_header=accept_header,
                content_type='',
                content_length=0,
                status_code=0,
                content_hash='',
                html_path='',
                response_time_ms=0
            )
            
            if accept_header == 'text/html':
                baseline_format = format_response
            else:
                alternative_formats.append(format_response)
    
    # Calculate scores
    format_availability_score = _calculate_format_availability_score(baseline_format, alternative_formats)
    content_consistency_score = _calculate_content_consistency_score(baseline_format, alternative_formats)
    agent_optimization_detected = _detect_agent_optimization(baseline_format, alternative_formats)
    
    return ContentNegotiationResult(
        url=url,
        timestamp=timestamp,
        baseline_format=baseline_format,
        alternative_formats=alternative_formats,
        format_availability_score=format_availability_score,
        content_consistency_score=content_consistency_score,
        agent_optimization_detected=agent_optimization_detected
    )


def _calculate_format_availability_score(baseline: FormatResponse, alternatives: List[FormatResponse]) -> float:
    """Calculate score based on format variety and success."""
    if not baseline or baseline.status_code != 200:
        return 0.0  # Site not accessible
    
    score = 50.0  # Base score for working HTML
    
    successful_formats = [fmt for fmt in alternatives if fmt.status_code == 200]
    
    # Bonus points per working alternative format
    score += len(successful_formats) * 12.5  # Max 50 pts for 4 alternatives
    
    # Quality bonus for specific formats  
    for fmt in successful_formats:
        if 'markdown' in fmt.content_type or fmt.accept_header == 'text/markdown':
            score += 10  # Markdown is ideal for agents
        elif 'json' in fmt.content_type:
            score += 5   # Structured data bonus 
        elif 'plain' in fmt.content_type:
            score += 3   # Plain text bonus
    
    return min(score, 100.0)


def _calculate_content_consistency_score(baseline: FormatResponse, alternatives: List[FormatResponse]) -> float:
    """Calculate score based on content differentiation across formats.""" 
    if not baseline or baseline.status_code != 200:
        return 0.0
        
    successful_alternatives = [fmt for fmt in alternatives if fmt.status_code == 200]
    
    if not successful_alternatives:
        return 100.0  # Only HTML works, so consistency is perfect
    
    # Check for identical content (bad - indicates no real content negotiation)
    identical_count = sum(1 for fmt in successful_alternatives 
                         if fmt.content_hash == baseline.content_hash)
    
    # Score based on content differentiation
    total_alternatives = len(successful_alternatives)
    different_content_ratio = (total_alternatives - identical_count) / total_alternatives
    
    # High score when content is actually different across formats
    return different_content_ratio * 100.0


def _detect_agent_optimization(baseline: FormatResponse, alternatives: List[FormatResponse]) -> bool:
    """Detect if site appears optimized for AI agents."""
    if not baseline or baseline.status_code != 200:
        return False
    
    # Look for signals of agent-friendly optimization
    successful_alternatives = [fmt for fmt in alternatives if fmt.status_code == 200]
    
    # Strong signals: Multiple working formats + actually different content
    if len(successful_alternatives) >= 2:
        different_content = any(fmt.content_hash != baseline.content_hash 
                              for fmt in successful_alternatives)
        if different_content:
            return True
    
    # Check for markdown availability (strong agent-friendly signal)
    markdown_available = any(fmt.status_code == 200 and 
                           ('markdown' in fmt.content_type or fmt.accept_header == 'text/markdown')
                           for fmt in successful_alternatives)
    
    return markdown_available