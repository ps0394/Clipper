#!/usr/bin/env python3
"""Direct LLM performance testing for agent-readiness validation."""

import json
import argparse
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import time
import hashlib

@dataclass
class AgentPerformanceTest:
    url: str
    query: str
    expected_type: str  # 'steps', 'prerequisites', 'code_example', 'troubleshooting'
    ground_truth_keywords: List[str]  # Keywords that should appear in good response

@dataclass  
class AgentPerformanceResult:
    url: str
    query: str
    response: str
    response_length: int
    contains_keywords: int
    total_keywords: int
    keyword_coverage: float
    response_quality_score: float  # 0-100
    extraction_success: bool
    response_time: float

def load_html_content(snapshots_dir: str) -> Dict[str, str]:
    """Load HTML content from Clipper snapshots directory."""
    
    snapshots_path = Path(snapshots_dir)
    
    # Load crawl results to map filenames to URLs
    crawl_file = snapshots_path / "crawl_results.json"
    if not crawl_file.exists():
        crawl_file = snapshots_path.parent / "crawl_results.json"
    
    if not crawl_file.exists():
        raise FileNotFoundError(f"Cannot find crawl_results.json in {snapshots_dir}")
    
    with open(crawl_file) as f:
        crawl_data = json.load(f)
    
    # Create filename -> URL mapping
    url_map = {}
    for item in crawl_data:
        filename = item['html_path']
        url = item['url']  
        url_map[filename] = url
    
    # Load HTML files
    html_content = {}
    for html_file in snapshots_path.glob("*.html"):
        filename = html_file.name
        if filename in url_map:
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                html_content[url_map[filename]] = content
            except Exception as e:
                print(f"⚠️  Could not read {html_file}: {e}")
    
    return html_content

def simulate_llm_extraction(html_content: str, query: str) -> str:
    """
    Simulate LLM content extraction and query response.
    
    In a real implementation, this would send to OpenAI/Claude API.
    For now, we simulate by extracting text and doing keyword matching.
    """
    
    # Simple text extraction (simulate what an LLM might see)
    from bs4 import BeautifulSoup
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script/style tags (what LLMs would ignore)
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Extract main content areas first
        main_content = ""
        for tag in ['main', 'article', '[role="main"]']:
            elements = soup.select(tag)
            if elements:
                main_content = ' '.join([elem.get_text(strip=True) for elem in elements])
                break
        
        # Fallback to body content
        if not main_content:
            main_content = soup.get_text(strip=True)
        
        # Simulate LLM processing: extract relevant sections based on query type
        if "get started" in query.lower() or "steps" in query.lower():
            # Look for numbered lists, headings with "start", etc.
            sections = extract_getting_started_content(soup)
        elif "prerequisite" in query.lower():
            sections = extract_prerequisites_content(soup)
        elif "code example" in query.lower():
            sections = extract_code_examples(soup)
        elif "troubleshoot" in query.lower():
            sections = extract_troubleshooting_content(soup)
        else:
            sections = main_content[:2000]  # First 2000 chars as default
        
        return sections
    
    except Exception as e:
        print(f"⚠️  Content extraction failed: {e}")
        return ""

def extract_getting_started_content(soup) -> str:
    """Extract getting started / setup instructions."""
    
    content_pieces = []
    
    # Look for headings with "start", "setup", "install", "quick"
    start_keywords = ['start', 'setup', 'install', 'quick', 'begin', 'first', 'initial']
    
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
        heading_text = heading.get_text().lower()
        if any(keyword in heading_text for keyword in start_keywords):
            # Get content after this heading
            content = extract_content_after_heading(heading)
            content_pieces.append(f"## {heading.get_text()}\n{content}")
    
    # Look for ordered lists (common for step-by-step instructions)
    for ol in soup.find_all('ol'):
        if len(ol.find_all('li')) >= 3:  # At least 3 steps
            steps = [li.get_text(strip=True) for li in ol.find_all('li')]
            content_pieces.append("Steps:\n" + "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps)))
    
    return "\n\n".join(content_pieces[:3])  # Top 3 relevant sections

def extract_prerequisites_content(soup) -> str:
    """Extract prerequisites and requirements."""
    
    content_pieces = []
    
    prereq_keywords = ['prerequisite', 'requirement', 'need', 'before', 'install', 'setup']
    
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
        heading_text = heading.get_text().lower()
        if any(keyword in heading_text for keyword in prereq_keywords):
            content = extract_content_after_heading(heading)
            content_pieces.append(f"## {heading.get_text()}\n{content}")
    
    # Look for lists that might contain requirements
    for ul in soup.find_all(['ul', 'ol']):
        items = [li.get_text(strip=True) for li in ul.find_all('li')]
        if len(items) >= 2 and any(any(kw in item.lower() for kw in ['version', 'install', 'require']) for item in items):
            content_pieces.append("Requirements:\n" + "\n".join(f"- {item}" for item in items))
            break
    
    return "\n\n".join(content_pieces[:2])

def extract_code_examples(soup) -> str:
    """Extract code examples and snippets."""
    
    content_pieces = []
    
    # Find code blocks
    for code in soup.find_all(['code', 'pre']):
        code_text = code.get_text(strip=True)
        if len(code_text) > 20:  # Substantial code block
            content_pieces.append(f"```\n{code_text}\n```")
    
    # Look for headings about examples
    example_keywords = ['example', 'sample', 'demo', 'tutorial', 'usage']
    
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
        heading_text = heading.get_text().lower()
        if any(keyword in heading_text for keyword in example_keywords):
            content = extract_content_after_heading(heading)
            content_pieces.append(f"## {heading.get_text()}\n{content}")
    
    return "\n\n".join(content_pieces[:3])

def extract_troubleshooting_content(soup) -> str:
    """Extract troubleshooting and error resolution info."""
    
    content_pieces = []
    
    trouble_keywords = ['troubleshoot', 'error', 'problem', 'issue', 'fix', 'solution', 'debug']
    
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
        heading_text = heading.get_text().lower()
        if any(keyword in heading_text for keyword in trouble_keywords):
            content = extract_content_after_heading(heading)
            content_pieces.append(f"## {heading.get_text()}\n{content}")
    
    return "\n\n".join(content_pieces[:3])

def extract_content_after_heading(heading) -> str:
    """Extract content that appears after a heading until next heading."""
    
    content_pieces = []
    current = heading.next_sibling
    
    while current and len(content_pieces) < 5:  # Limit content length
        if current.name and current.name.startswith('h'):  # Hit next heading
            break
        if hasattr(current, 'get_text'):
            text = current.get_text(strip=True)
            if text and len(text) > 20:
                content_pieces.append(text)
        current = current.next_sibling
    
    return "\n".join(content_pieces)

def evaluate_response_quality(response: str, expected_keywords: List[str], query_type: str) -> Tuple[float, int, bool]:
    """Evaluate the quality of the extracted response."""
    
    if not response or len(response.strip()) < 50:
        return 0.0, 0, False
    
    response_lower = response.lower()
    
    # Count keyword matches
    keyword_matches = sum(1 for keyword in expected_keywords if keyword.lower() in response_lower)
    keyword_coverage = keyword_matches / len(expected_keywords) if expected_keywords else 0
    
    # Base quality scoring
    quality_score = 0.0
    
    # Length factor (reasonable response length)
    if 100 <= len(response) <= 2000:
        quality_score += 30.0
    elif len(response) > 50:
        quality_score += 15.0
    
    # Keyword coverage factor
    quality_score += keyword_coverage * 40.0
    
    # Query-specific factors
    if query_type == 'steps' and any(indicator in response_lower for indicator in ['step', '1.', 'first', 'then']):
        quality_score += 20.0
    elif query_type == 'code_example' and any(indicator in response for indicator in ['```', 'code', 'function', 'class']):
        quality_score += 20.0
    elif query_type == 'prerequisites' and any(indicator in response_lower for indicator in ['need', 'install', 'require', 'version']):
        quality_score += 20.0
    elif query_type == 'troubleshooting' and any(indicator in response_lower for indicator in ['error', 'problem', 'solution', 'fix']):
        quality_score += 20.0
    
    # Structure indicators (headings, lists)
    if any(indicator in response for indicator in ['##', '-', '1.', '2.']):
        quality_score += 10.0
    
    extraction_success = quality_score >= 60.0 and len(response) >= 100
    
    return min(quality_score, 100.0), keyword_matches, extraction_success

# Standard test queries for documentation sites
STANDARD_TEST_QUERIES = {
    'getting_started': AgentPerformanceTest(
        url="", 
        query="What are the main steps to get started?",
        expected_type="steps",
        ground_truth_keywords=["install", "setup", "configure", "first", "step", "start"]
    ),
    'prerequisites': AgentPerformanceTest(
        url="",
        query="What are the prerequisites and requirements?", 
        expected_type="prerequisites",
        ground_truth_keywords=["require", "need", "install", "version", "dependency", "prerequisite"]
    ),
    'code_example': AgentPerformanceTest(
        url="",
        query="Provide a code example or sample usage",
        expected_type="code_example", 
        ground_truth_keywords=["example", "code", "sample", "function", "import", "class"]
    ),
    'troubleshooting': AgentPerformanceTest(
        url="",
        query="What are common troubleshooting issues and solutions?",
        expected_type="troubleshooting",
        ground_truth_keywords=["error", "problem", "issue", "solution", "fix", "debug"]
    )
}

def run_agent_performance_tests(snapshots_dir: str) -> List[AgentPerformanceResult]:
    """Run agent performance tests on HTML content."""
    
    print("🔄 Loading HTML content...")
    html_content = load_html_content(snapshots_dir)
    
    print(f"🧠 Running agent performance tests on {len(html_content)} sites...")
    
    results = []
    
    for url, html in html_content.items():
        print(f"  Testing: {url}")
        
        for test_name, test_template in STANDARD_TEST_QUERIES.items():
            start_time = time.time()
            
            # Create test for this URL
            test = AgentPerformanceTest(
                url=url,
                query=test_template.query,
                expected_type=test_template.expected_type,
                ground_truth_keywords=test_template.ground_truth_keywords
            )
            
            # Simulate LLM extraction
            response = simulate_llm_extraction(html, test.query)
            response_time = time.time() - start_time
            
            # Evaluate response quality
            quality_score, keyword_matches, extraction_success = evaluate_response_quality(
                response, test.ground_truth_keywords, test.expected_type
            )
            
            keyword_coverage = keyword_matches / len(test.ground_truth_keywords) if test.ground_truth_keywords else 0
            
            result = AgentPerformanceResult(
                url=url,
                query=test.query,
                response=response[:500],  # Truncate for storage
                response_length=len(response),
                contains_keywords=keyword_matches,
                total_keywords=len(test.ground_truth_keywords),
                keyword_coverage=keyword_coverage,
                response_quality_score=quality_score,
                extraction_success=extraction_success,
                response_time=response_time
            )
            
            results.append(result)
    
    return results

def generate_agent_performance_report(results: List[AgentPerformanceResult]) -> str:
    """Generate agent performance analysis report."""
    
    # Group results by URL
    by_url = {}
    for result in results:
        if result.url not in by_url:
            by_url[result.url] = []
        by_url[result.url].append(result)
    
    report = [
        "# Direct Agent Performance Testing Report",
        f"**Test Date:** {time.strftime('%Y-%m-%d')}",
        f"**Sites Tested:** {len(by_url)}",
        f"**Total Queries:** {len(results)}",
        ""
    ]
    
    # Overall statistics
    avg_quality = sum(r.response_quality_score for r in results) / len(results) if results else 0
    success_rate = sum(1 for r in results if r.extraction_success) / len(results) * 100 if results else 0
    avg_coverage = sum(r.keyword_coverage for r in results) / len(results) * 100 if results else 0
    
    report.extend([
        "## 📊 Overall Performance",
        f"- **Average Quality Score**: {avg_quality:.1f}/100",
        f"- **Extraction Success Rate**: {success_rate:.1f}%",
        f"- **Average Keyword Coverage**: {avg_coverage:.1f}%",
        ""
    ])
    
    # Results by site
    report.extend([
        "## 🔍 Site-by-Site Analysis",
        ""
    ])
    
    site_scores = []
    for url, site_results in by_url.items():
        site_avg_quality = sum(r.response_quality_score for r in site_results) / len(site_results)
        site_success_rate = sum(1 for r in site_results if r.extraction_success) / len(site_results) * 100
        
        site_scores.append((url, site_avg_quality))
        
        status = "✅" if site_success_rate >= 75 else "⚠️" if site_success_rate >= 50 else "❌"
        
        report.extend([
            f"### {url}",
            f"{status} **Overall Agent Performance**: {site_avg_quality:.1f}/100 ({site_success_rate:.1f}% success rate)",
            ""
        ])
        
        for result in site_results:
            query_type = result.query.split()[2:5]  # Extract query type
            query_desc = " ".join(query_type) if query_type else "query"
            status_icon = "✅" if result.extraction_success else "❌"
            
            report.extend([
                f"   {status_icon} **{query_desc}**: {result.response_quality_score:.1f}/100 "
                f"({result.contains_keywords}/{result.total_keywords} keywords, {result.response_length} chars)",
            ])
        
        report.append("")
    
    # Top/bottom performers  
    site_scores.sort(key=lambda x: x[1], reverse=True)
    
    report.extend([
        "## 🏆 Agent-Ready Ranking",
        ""
    ])
    
    for i, (url, score) in enumerate(site_scores, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📋"
        report.append(f"{emoji} **{i}. {url}**: {score:.1f}/100")
    
    return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description="Test direct agent performance on documentation sites")
    parser.add_argument("snapshots_dir", help="Directory containing HTML snapshots from Clipper evaluation")
    parser.add_argument("--output", "-o", help="Save performance report to file")
    parser.add_argument("--json-output", help="Save raw results as JSON")
    
    args = parser.parse_args()
    
    try:
        # Run agent performance tests
        results = run_agent_performance_tests(args.snapshots_dir)
        
        if not results:
            print("❌ No test results generated")
            return 1
        
        # Generate report
        report = generate_agent_performance_report(results)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report) 
            print(f"📄 Agent performance report saved to {args.output}")
        
        if args.json_output:
            # Convert to JSON-serializable format
            json_data = [
                {
                    'url': r.url,
                    'query': r.query, 
                    'response': r.response,
                    'response_length': r.response_length,
                    'contains_keywords': r.contains_keywords,
                    'total_keywords': r.total_keywords,
                    'keyword_coverage': r.keyword_coverage,
                    'response_quality_score': r.response_quality_score,
                    'extraction_success': r.extraction_success,
                    'response_time': r.response_time
                }
                for r in results
            ]
            
            with open(args.json_output, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print(f"📄 Raw data saved to {args.json_output}")
        
        print(report)
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())