#!/usr/bin/env python3
"""Compare YARA scores with Boilerpipe content extraction quality."""

import json
import argparse
import requests
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
import statistics
import hashlib

# Try to import boilerpy3, with fallback instructions
try:
    from boilerpy3 import extractors
    BOILERPIPE_AVAILABLE = True
except ImportError:
    BOILERPIPE_AVAILABLE = False
    print("⚠️  Warning: boilerpy3 not installed. Install with: pip install boilerpy3")

@dataclass
class BoilerplateExtraction:
    url: str
    original_length: int
    extracted_length: int
    extraction_ratio: float
    content_hash: str
    extraction_success: bool
    word_count: int

@dataclass
class YaraScore:
    url: str
    parseability_score: float
    content_density: float
    boilerplate_resistance: float
    failure_mode: str

def extract_with_boilerpipe(html_content: str) -> Dict:
    """Extract content using Boilerpipe and return metrics."""
    
    if not BOILERPIPE_AVAILABLE:
        return {
            'extracted_length': 0,
            'extraction_ratio': 0,
            'content_hash': '',
            'extraction_success': False,
            'word_count': 0
        }
    
    try:
        # Try ArticleExtractor first (most conservative)
        extractor = extractors.ArticleExtractor()
        extracted_text = extractor.get_content(html_content)
        
        if not extracted_text or len(extracted_text.strip()) < 100:
            # Fallback to DefaultExtractor  
            extractor = extractors.DefaultExtractor()
            extracted_text = extractor.get_content(html_content)
        
        if not extracted_text:
            extracted_text = ""
        
        extracted_length = len(extracted_text)
        extraction_ratio = extracted_length / len(html_content) if len(html_content) > 0 else 0
        content_hash = hashlib.md5(extracted_text.encode()).hexdigest()
        extraction_success = extracted_length > 100  # Minimum content threshold
        word_count = len(extracted_text.split())
        
        return {
            'extracted_length': extracted_length,
            'extraction_ratio': extraction_ratio,
            'content_hash': content_hash,
            'extraction_success': extraction_success,
            'word_count': word_count
        }
    
    except Exception as e:
        print(f"⚠️  Boilerpipe extraction failed: {e}")
        return {
            'extracted_length': 0,
            'extraction_ratio': 0,
            'content_hash': '',
            'extraction_success': False,
            'word_count': 0
        }

def load_html_snapshots(snapshots_dir: str) -> Dict[str, str]:
    """Load HTML snapshots and map to URLs."""
    
    snapshots_path = Path(snapshots_dir)
    
    # Load crawl results to map filenames to URLs
    crawl_file = snapshots_path / "crawl_results.json"
    if not crawl_file.exists():
        # Try parent directory
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

def load_yara_results(results_dir: str) -> List[YaraScore]:
    """Load YARA results from evaluation directory."""
    
    results_path = Path(results_dir)
    scores_file = None
    crawl_file = None
    
    # Find scores and crawl files
    for pattern in ['*_scores.json', 'scores.json']:
        matches = list(results_path.glob(pattern))
        if matches:
            scores_file = matches[0]
            break
    
    for pattern in ['*/crawl_results.json', 'snapshots/crawl_results.json', 'crawl_results.json']:
        matches = list(results_path.glob(pattern))
        if matches:
            crawl_file = matches[0]
            break
    
    if not scores_file or not crawl_file:
        raise FileNotFoundError(f"Cannot find YARA results in {results_dir}")
    
    # Load URLs
    with open(crawl_file) as f:
        crawl_data = json.load(f)
        urls = [item['url'] for item in crawl_data]
    
    # Load scores  
    with open(scores_file) as f:
        scores_data = json.load(f)
    
    yara_scores = []
    for i, score_data in enumerate(scores_data):
        if i < len(urls):
            subscores = score_data.get('subscores', {})
            yara_scores.append(YaraScore(
                url=urls[i],
                parseability_score=score_data['parseability_score'],
                content_density=subscores.get('content_density', 0),
                boilerplate_resistance=subscores.get('boilerplate_resistance', 0),
                failure_mode=score_data['failure_mode']
            ))
    
    return yara_scores

def run_boilerpipe_comparison(yara_results_dir: str) -> Dict:
    """Run comprehensive YARA vs Boilerpipe comparison."""
    
    print("🔄 Loading YARA results...")
    yara_scores = load_yara_results(yara_results_dir)
    
    # Determine snapshots directory
    results_path = Path(yara_results_dir)
    snapshots_dir = results_path / "snapshots"
    if not snapshots_dir.exists():
        snapshots_dir = results_path
    
    print(f"📄 Loading HTML snapshots from {snapshots_dir}...")
    html_content = load_html_snapshots(str(snapshots_dir))
    
    print(f"🔍 Running Boilerpipe extraction on {len(html_content)} pages...")
    
    boilerpipe_results = []
    
    for url, html in html_content.items():
        print(f"  Extracting: {url}")
        
        extraction_metrics = extract_with_boilerpipe(html)
        
        boilerpipe_results.append(BoilerplateExtraction(
            url=url,
            original_length=len(html),
            extracted_length=extraction_metrics['extracted_length'],
            extraction_ratio=extraction_metrics['extraction_ratio'],
            content_hash=extraction_metrics['content_hash'],
            extraction_success=extraction_metrics['extraction_success'],
            word_count=extraction_metrics['word_count']
        ))
    
    return {
        'yara_scores': yara_scores,
        'boilerpipe_results': boilerpipe_results
    }

def calculate_correlation(x_values: List[float], y_values: List[float]) -> Tuple[float, float]:
    """Calculate Pearson correlation coefficient."""
    
    if len(x_values) != len(y_values) or len(x_values) < 3:
        return 0.0, 1.0
    
    try:
        mean_x = statistics.mean(x_values)
        mean_y = statistics.mean(y_values)
        
        numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values))
        
        sum_sq_x = sum((x - mean_x) ** 2 for x in x_values)
        sum_sq_y = sum((y - mean_y) ** 2 for y in y_values)
        
        denominator = (sum_sq_x * sum_sq_y) ** 0.5
        
        if denominator == 0:
            return 0.0, 1.0
        
        correlation = numerator / denominator
        
        # Rough p-value estimate
        n = len(x_values)
        t_stat = abs(correlation) * ((n - 2) / (1 - correlation**2)) ** 0.5 if correlation != 1 else float('inf')
        p_value = max(0.001, 2 * (1 - min(0.999, t_stat / (n ** 0.5))))
        
        return correlation, p_value
    
    except (ValueError, ZeroDivisionError):
        return 0.0, 1.0

def generate_boilerpipe_report(comparison_data: Dict) -> str:
    """Generate human-readable Boilerpipe comparison report."""
    
    yara_scores = comparison_data['yara_scores']
    boilerpipe_results = comparison_data['boilerpipe_results']
    
    # Match YARA and Boilerpipe results by URL
    matched_data = []
    for yara in yara_scores:
        boilerpipe = next((bp for bp in boilerpipe_results if bp.url == yara.url), None)
        if boilerpipe:
            matched_data.append((yara, boilerpipe))
    
    report = [
        "# YARA vs Boilerpipe Content Extraction Comparison",
        f"**Analysis Date:** {Path.cwd()}",
        f"**Sample Size:** {len(matched_data)} URLs",
        ""
    ]
    
    if not BOILERPIPE_AVAILABLE:
        report.extend([
            "❌ **Boilerpipe Not Available**",
            "Install boilerpy3 to run this comparison: `pip install boilerpy3`",
            ""
        ])
        return "\n".join(report)
    
    # Calculate correlations
    yara_content_density = [yara.content_density for yara, _ in matched_data]
    yara_boilerplate_resistance = [yara.boilerplate_resistance for yara, _ in matched_data]
    yara_overall = [yara.parseability_score for yara, _ in matched_data]
    
    boilerpipe_ratios = [bp.extraction_ratio * 100 for _, bp in matched_data]
    boilerpipe_success = [100 if bp.extraction_success else 0 for _, bp in matched_data]
    boilerpipe_word_counts = [bp.word_count for _, bp in matched_data]
    
    # Correlations
    corr_density_ratio, p_density = calculate_correlation(yara_content_density, boilerpipe_ratios)
    corr_boilerplate_success, p_boil_success = calculate_correlation(yara_boilerplate_resistance, boilerpipe_success)
    corr_overall_ratio, p_overall = calculate_correlation(yara_overall, boilerpipe_ratios)
    
    report.extend([
        "## 📊 Correlation Analysis",
        f"- **YARA Content Density ↔ Boilerpipe Extraction Ratio**: r = {corr_density_ratio:.3f} (p = {p_density:.3f})",
        f"- **YARA Boilerplate Resistance ↔ Boilerpipe Success**: r = {corr_boilerplate_success:.3f} (p = {p_boil_success:.3f})",
        f"- **YARA Overall Score ↔ Boilerpipe Extraction Ratio**: r = {corr_overall_ratio:.3f} (p = {p_overall:.3f})",
        ""
    ])
    
    # Extraction success analysis
    successful_extractions = [bp for _, bp in matched_data if bp.extraction_success]
    success_rate = len(successful_extractions) / len(matched_data) * 100
    
    avg_extraction_ratio = statistics.mean(boilerpipe_ratios) if boilerpipe_ratios else 0
    avg_word_count = statistics.mean(boilerpipe_word_counts) if boilerpipe_word_counts else 0
    
    report.extend([
        "## 🔍 Boilerpipe Extraction Analysis", 
        f"- **Success Rate**: {len(successful_extractions)}/{len(matched_data)} ({success_rate:.1f}%)",
        f"- **Average Extraction Ratio**: {avg_extraction_ratio:.1f}%",
        f"- **Average Word Count**: {avg_word_count:.0f} words",
        ""
    ])
    
    # Individual site analysis
    report.extend([
        "## 📋 Individual Site Analysis",
        ""
    ])
    
    # Sort by YARA score for comparison
    matched_data.sort(key=lambda x: x[0].parseability_score, reverse=True)
    
    for yara, boilerpipe in matched_data:
        status = "✅" if boilerpipe.extraction_success else "❌"
        report.extend([
            f"### {yara.url}",
            f"{status} **YARA**: {yara.parseability_score:.1f}/100 (density: {yara.content_density:.1f}, boilerplate: {yara.boilerplate_resistance:.1f})",
            f"   **Boilerpipe**: {boilerpipe.extraction_ratio*100:.1f}% extracted ({boilerpipe.word_count} words)",
            ""
        ])
    
    # Validation conclusion
    report.extend([
        "## 🎯 Validation Assessment",
        ""
    ])
    
    strong_correlations = sum(1 for r in [corr_density_ratio, corr_boilerplate_success, corr_overall_ratio] if abs(r) > 0.6)
    
    if strong_correlations >= 2:
        report.append("✅ **STRONG VALIDATION**: YARA content analysis correlates well with Boilerpipe extraction quality.")
    elif strong_correlations >= 1 or max(abs(corr_density_ratio), abs(corr_overall_ratio)) > 0.4:
        report.append("⚠️ **MODERATE VALIDATION**: YARA shows reasonable correlation with content extraction success.")  
    else:
        report.append("❌ **WEAK VALIDATION**: YARA content analysis needs improvement compared to Boilerpipe standards.")
    
    return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description="Compare YARA scores with Boilerpipe content extraction")
    parser.add_argument("yara_results", help="Directory containing YARA evaluation results") 
    parser.add_argument("--output", "-o", help="Save comparison report to file")
    parser.add_argument("--json-output", help="Save raw data as JSON")
    
    args = parser.parse_args()
    
    try:
        # Run comparison
        comparison_data = run_boilerpipe_comparison(args.yara_results)
        
        # Generate report
        report = generate_boilerpipe_report(comparison_data)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 Comparison report saved to {args.output}")
        
        if args.json_output:
            # Convert dataclasses to dicts for JSON serialization
            json_data = {
                'yara_scores': [score.__dict__ for score in comparison_data['yara_scores']],
                'boilerpipe_results': [result.__dict__ for result in comparison_data['boilerpipe_results']]
            }
            
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