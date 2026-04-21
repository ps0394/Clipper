"""HTML parsing and parseability signal extraction."""

import json
from pathlib import Path
from typing import Dict, List, Any
from bs4 import BeautifulSoup
import re

from .schemas import ParseSignals, ParseResult


def parse_snapshots(snapshots_dir: str, output_file: str) -> None:
    """Parse HTML snapshots and extract parseability signals.
    
    Args:
        snapshots_dir: Directory containing HTML snapshot files
        output_file: JSON file to save parse results
    """
    snapshots_path = Path(snapshots_dir)
    if not snapshots_path.exists():
        raise FileNotFoundError(f"Snapshots directory not found: {snapshots_dir}")
    
    # Load crawl results to get HTML file mappings
    crawl_results_file = snapshots_path / "crawl_results.json"
    if not crawl_results_file.exists():
        raise FileNotFoundError(f"Crawl results not found: {crawl_results_file}")
    
    with open(crawl_results_file, 'r', encoding='utf-8') as f:
        crawl_results = json.load(f)
    
    results = []
    
    for crawl_result in crawl_results:
        if crawl_result['html_path']:  # Only parse successful crawls
            html_file = snapshots_path / crawl_result['html_path']
            if html_file.exists():
                print(f"Parsing: {crawl_result['url']}")
                result = _parse_html_file(html_file)
                results.append(result)
            else:
                print(f"Warning: HTML file not found: {html_file}")
    
    # Save parse results
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump([result.to_dict() for result in results], f, indent=2)
    
    print(f"Parsed {len(results)} HTML files, results saved to {output_file}")


def _parse_html_file(html_file: Path) -> ParseResult:
    """Parse a single HTML file and extract signals.
    
    Args:
        html_file: Path to HTML file
        
    Returns:
        ParseResult with extracted signals and evidence
    """
    with open(html_file, 'r', encoding='utf-8', errors='replace') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract parseability signals
    signals = _extract_parseability_signals(soup)
    
    # Gather evidence for signals
    evidence = _gather_evidence(soup)
    
    return ParseResult(
        html_path=str(html_file.resolve()),
        signals=signals,
        evidence=evidence
    )


def _extract_parseability_signals(soup: BeautifulSoup) -> ParseSignals:
    """Extract deterministic parseability signals from parsed HTML.
    
    Args:
        soup: BeautifulSoup parsed HTML
        
    Returns:
        ParseSignals with raw signal values
    """
    # Check for semantic content elements
    has_main = bool(soup.find('main'))
    has_article = bool(soup.find('article'))
    
    # Validate heading hierarchy
    heading_hierarchy_valid = _validate_heading_hierarchy(soup)
    
    # Calculate text density ratio
    text_density_ratio = _calculate_text_density(soup)
    
    # Count code blocks and tables
    code_blocks_count = len(soup.find_all(['pre', 'code']))
    tables_count = len(soup.find_all('table'))
    
    # Estimate boilerplate leakage
    boilerplate_leakage_estimate = _estimate_boilerplate_leakage(soup)
    
    # Detect agent content hints
    agent_content_hints = _detect_agent_content_hints(soup)
    
    return ParseSignals(
        has_main_element=has_main,
        has_article_element=has_article,
        heading_hierarchy_valid=heading_hierarchy_valid,
        text_density_ratio=text_density_ratio,
        code_blocks_count=code_blocks_count,
        tables_count=tables_count,
        boilerplate_leakage_estimate=boilerplate_leakage_estimate,
        agent_content_hints=agent_content_hints
    )


def _validate_heading_hierarchy(soup: BeautifulSoup) -> bool:
    """Check if heading hierarchy follows H1 → H2 → H3 pattern.
    
    Args:
        soup: BeautifulSoup parsed HTML
        
    Returns:
        True if hierarchy is valid, False otherwise
    """
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    if not headings:
        return False  # No headings found
    
    # Extract heading levels
    levels = []
    for heading in headings:
        level = int(heading.name[1])
        levels.append(level)
    
    # Check for valid progression (no jumps > 1 level)
    for i in range(1, len(levels)):
        if levels[i] > levels[i-1] + 1:
            return False
    
    return True


def _calculate_text_density(soup: BeautifulSoup) -> float:
    """Calculate ratio of primary content text to total DOM size.
    
    Args:
        soup: BeautifulSoup parsed HTML
        
    Returns:
        Text density ratio (0.0 to 1.0)
    """
    # Get total text content
    total_text = soup.get_text(strip=True)
    if not total_text:
        return 0.0
    
    # Try to find primary content area
    primary_content = ""
    
    # Look for main content containers (in priority order)
    content_selectors = ['main', 'article', '.content', '#content', '.main-content']
    
    for selector in content_selectors:
        elements = soup.select(selector)
        if elements:
            primary_content = elements[0].get_text(strip=True)
            break
    
    # Fallback to body content if no content area found
    if not primary_content:
        body = soup.find('body')
        if body:
            primary_content = body.get_text(strip=True)
        else:
            primary_content = total_text
    
    # Calculate density ratio
    if len(total_text) == 0:
        return 0.0
        
    return min(len(primary_content) / len(total_text), 1.0)


def _estimate_boilerplate_leakage(soup: BeautifulSoup) -> float:
    """Estimate how much of the content is boilerplate (nav/footer/sidebar).
    
    Args:
        soup: BeautifulSoup parsed HTML
        
    Returns:
        Boilerplate leakage estimate (0.0 to 1.0, higher = more boilerplate)
    """
    total_text = soup.get_text(strip=True)
    if not total_text:
        return 1.0  # All boilerplate if no text
    
    # Find common boilerplate elements
    boilerplate_selectors = [
        'nav', 'header', 'footer', 'aside', 
        '.nav', '.navigation', '.sidebar', '.menu',
        '.header', '.footer', '.breadcrumb'
    ]
    
    boilerplate_text = ""
    for selector in boilerplate_selectors:
        elements = soup.select(selector)
        for element in elements:
            boilerplate_text += element.get_text(strip=True)
    
    # Calculate boilerplate ratio
    if len(total_text) == 0:
        return 1.0
        
    return min(len(boilerplate_text) / len(total_text), 1.0)


def _gather_evidence(soup: BeautifulSoup) -> Dict[str, Any]:
    """Gather evidence supporting the extracted signals.
    
    Args:
        soup: BeautifulSoup parsed HTML
        
    Returns:
        Dictionary with evidence details
    """
    evidence = {}
    
    # Semantic elements evidence
    main_elements = soup.find_all('main')
    article_elements = soup.find_all('article')
    
    evidence['semantic_elements'] = {
        'main_count': len(main_elements),
        'article_count': len(article_elements)
    }
    
    # Heading structure evidence
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    heading_structure = []
    for heading in headings[:10]:  # Limit to first 10 for evidence
        heading_structure.append({
            'level': int(heading.name[1]),
            'text': heading.get_text(strip=True)[:50]  # Limit text length
        })
    
    evidence['heading_structure'] = heading_structure
    
    # Content structure evidence
    evidence['content_structure'] = {
        'total_paragraphs': len(soup.find_all('p')),
        'total_divs': len(soup.find_all('div')),
        'code_elements': len(soup.find_all(['pre', 'code'])),
        'table_elements': len(soup.find_all('table')),
        'list_elements': len(soup.find_all(['ul', 'ol']))
    }
    
    return evidence


def _detect_agent_content_hints(soup: BeautifulSoup) -> Dict[str, Any]:
    """Detect agent-friendly content hints in HTML.
    
    Scans for signals that a site explicitly supports machine-readable
    content formats: alternate format links, markdown URLs, LLM hints,
    and llms.txt references.
    """
    hints = {
        'has_markdown_alternate': False,
        'has_markdown_url_meta': False,
        'has_llm_hints': False,
        'has_llms_txt_ref': False,
        'has_non_html_alternate': False,
        'details': []
    }

    # Check <link rel="alternate"> elements
    for link in soup.find_all('link', rel=lambda r: r and 'alternate' in r):
        link_type = (link.get('type') or '').lower()
        href = link.get('href', '')

        if 'markdown' in link_type:
            hints['has_markdown_alternate'] = True
            hints['details'].append(f'link rel=alternate type={link_type} href={href[:80]}')

        elif link_type and 'html' not in link_type and 'rss' not in link_type and 'atom' not in link_type:
            # Non-HTML, non-feed alternate (e.g. application/json)
            hints['has_non_html_alternate'] = True
            hints['details'].append(f'link rel=alternate type={link_type} href={href[:80]}')

        # data-llm-hint on any <link>
        if link.get('data-llm-hint'):
            hints['has_llm_hints'] = True
            hints['details'].append(f'data-llm-hint: {link["data-llm-hint"][:100]}')

    # Check <link rel="index"> with llms.txt reference
    for link in soup.find_all('link', rel=lambda r: r and 'index' in r):
        href = (link.get('href') or '').lower()
        if 'llms' in href:
            hints['has_llms_txt_ref'] = True
            hints['details'].append(f'llms.txt ref: {link.get("href", "")[:100]}')
        if link.get('data-llm-hint'):
            hints['has_llm_hints'] = True
            hints['details'].append(f'data-llm-hint: {link["data-llm-hint"][:100]}')

    # Check <meta name="markdown_url">
    md_meta = soup.find('meta', attrs={'name': lambda n: n and n.lower() == 'markdown_url'})
    if md_meta and md_meta.get('content'):
        hints['has_markdown_url_meta'] = True
        hints['details'].append(f'meta markdown_url: {md_meta["content"][:100]}')

    # Check <a> or <link> referencing llms.txt anywhere
    if not hints['has_llms_txt_ref']:
        for tag in soup.find_all(['a', 'link'], href=True):
            if 'llms.txt' in (tag['href'] or '').lower():
                hints['has_llms_txt_ref'] = True
                hints['details'].append(f'llms.txt link: {tag["href"][:100]}')
                break

    return hints