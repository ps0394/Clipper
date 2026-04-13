#!/usr/bin/env python3
"""Lighthouse comparison using PageSpeed Insights API (no local installation needed)."""

import json
import requests
import argparse
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import statistics

@dataclass
class LighthouseScore:
    url: str
    accessibility: float
    seo: float 
    best_practices: float
    performance: float
    pwa: float

@dataclass
class YaraScore:
    url: str
    parseability_score: float
    semantic_structure: float
    heading_hierarchy: float
    content_density: float
    rich_content: float
    boilerplate_resistance: float
    failure_mode: str

def get_lighthouse_scores_via_api(url: str, api_key: Optional[str] = None) -> LighthouseScore:
    """Get Lighthouse scores via PageSpeed Insights API."""
    
    # PageSpeed Insights API endpoint
    api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    
    params = {
        'url': url,
        'category': ['accessibility', 'seo', 'best-practices', 'performance', 'pwa'],
        'strategy': 'desktop'
    }
    
    if api_key:
        params['key'] = api_key
    
    try:
        print(f"  Calling PageSpeed Insights API for {url}")
        response = requests.get(api_url, params=params, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract lighthouse scores from PageSpeed response
            categories = data.get('lighthouseResult', {}).get('categories', {})
            
            return LighthouseScore(
                url=url,
                accessibility=categories.get('accessibility', {}).get('score', 0) * 100,
                seo=categories.get('seo', {}).get('score', 0) * 100,
                best_practices=categories.get('best-practices', {}).get('score', 0) * 100,
                performance=categories.get('performance', {}).get('score', 0) * 100,
                pwa=categories.get('pwa', {}).get('score', 0) * 100
            )
        elif response.status_code == 429:
            print(f"  ⚠️ Rate limited for {url}, retrying in 10s...")
            time.sleep(10)
            return get_lighthouse_scores_via_api(url, api_key)  # Retry once
        else:
            print(f"  ❌ API error for {url}: {response.status_code}")
            return LighthouseScore(url, 0, 0, 0, 0, 0)
    
    except Exception as e:
        print(f"  ❌ Exception for {url}: {e}")
        return LighthouseScore(url, 0, 0, 0, 0, 0)

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
                semantic_structure=subscores.get('semantic_structure', 0),
                heading_hierarchy=subscores.get('heading_hierarchy', 0), 
                content_density=subscores.get('content_density', 0),
                rich_content=subscores.get('rich_content', 0),
                boilerplate_resistance=subscores.get('boilerplate_resistance', 0),
                failure_mode=score_data['failure_mode']
            ))
    
    return yara_scores

def calculate_correlation(x_values: List[float], y_values: List[float]) -> Tuple[float, float]:
    """Calculate Pearson correlation coefficient and p-value estimate."""
    
    if len(x_values) != len(y_values) or len(x_values) < 3:
        return 0.0, 1.0
    
    # Remove pairs with zero values (failed evaluations)
    pairs = [(x, y) for x, y in zip(x_values, y_values) if x > 0 and y > 0]
    
    if len(pairs) < 3:
        return 0.0, 1.0
    
    x_clean, y_clean = zip(*pairs)
    
    try:
        mean_x = statistics.mean(x_clean)
        mean_y = statistics.mean(y_clean)
        
        numerator = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
        
        sum_sq_x = sum((x - mean_x) ** 2 for x in x_clean)
        sum_sq_y = sum((y - mean_y) ** 2 for y in y_clean)
        
        denominator = (sum_sq_x * sum_sq_y) ** 0.5
        
        if denominator == 0:
            return 0.0, 1.0
        
        correlation = numerator / denominator
        
        # Rough p-value estimate
        n = len(pairs)
        t_stat = abs(correlation) * ((n - 2) / (1 - correlation**2)) ** 0.5 if abs(correlation) < 1 else float('inf')
        p_value = max(0.001, 2 * (1 - min(0.999, t_stat / (n ** 0.5))))
        
        return correlation, p_value
    
    except (ValueError, ZeroDivisionError):
        return 0.0, 1.0

def run_lighthouse_yara_comparison(yara_results_dir: str, api_key: Optional[str] = None) -> Dict:
    """Run comprehensive YARA vs Lighthouse comparison."""
    
    print("🔄 Loading YARA results...")
    yara_scores = load_yara_results(yara_results_dir)
    
    print(f"🌐 Running Lighthouse via PageSpeed Insights API on {len(yara_scores)} URLs...")
    if not api_key:
        print("⚠️  No API key provided - using free tier (rate limited)")
    
    lighthouse_scores = []
    
    for i, yara_score in enumerate(yara_scores, 1):
        print(f"  {i}/{len(yara_scores)}: {yara_score.url}")
        lighthouse_score = get_lighthouse_scores_via_api(yara_score.url, api_key)
        lighthouse_scores.append(lighthouse_score)
        
        # Rate limiting for free tier
        if not api_key and i < len(yara_scores):
            time.sleep(2)  # Be nice to free API
    
    print("🔍 Calculating correlations...")
    
    # Define correlation tests
    correlation_tests = [
        ('parseability_score', 'accessibility', 'YARA Overall vs Lighthouse Accessibility'),
        ('semantic_structure', 'accessibility', 'YARA Semantic vs Lighthouse Accessibility'),  
        ('semantic_structure', 'seo', 'YARA Semantic vs Lighthouse SEO'),
        ('heading_hierarchy', 'accessibility', 'YARA Headings vs Lighthouse Accessibility'),
        ('heading_hierarchy', 'seo', 'YARA Headings vs Lighthouse SEO'),
        ('content_density', 'seo', 'YARA Content Density vs Lighthouse SEO'),
        ('boilerplate_resistance', 'accessibility', 'YARA Boilerplate vs Lighthouse Accessibility'),
    ]
    
    correlations = []
    for yara_metric, lighthouse_metric, description in correlation_tests:
        yara_values = [getattr(score, yara_metric) for score in yara_scores]
        lighthouse_values = [getattr(score, lighthouse_metric) for score in lighthouse_scores]
        
        r, p = calculate_correlation(yara_values, lighthouse_values)
        
        correlations.append({
            'yara_metric': yara_metric,
            'lighthouse_metric': lighthouse_metric, 
            'description': description,
            'correlation': r,
            'p_value': p,
            'sample_size': len([y for y in yara_values if y > 0])
        })
        
        print(f"  {description}: r = {r:.3f} (p = {p:.3f})")
    
    return {
        'yara_scores': yara_scores,
        'lighthouse_scores': lighthouse_scores,
        'correlations': correlations
    }

def generate_lighthouse_comparison_report(comparison_data: Dict) -> str:
    """Generate comprehensive Lighthouse vs YARA comparison report."""
    
    correlations = comparison_data['correlations']
    yara_scores = comparison_data['yara_scores']
    lighthouse_scores = comparison_data['lighthouse_scores']
    
    report = [
        "# YARA vs Lighthouse Validation Report",
        f"**Analysis Date:** {time.strftime('%Y-%m-%d %H:%M')}",
        f"**Sample Size:** {len(yara_scores)} URLs",
        f"**Data Source:** Google PageSpeed Insights API (Lighthouse)",
        ""
    ]
    
    # Classification of correlations
    strong_correlations = [c for c in correlations if c['correlation'] > 0.6 and c['p_value'] < 0.05]
    moderate_correlations = [c for c in correlations if 0.4 <= c['correlation'] <= 0.6 and c['p_value'] < 0.05]
    weak_correlations = [c for c in correlations if c['correlation'] < 0.4 or c['p_value'] >= 0.05]
    
    # Summary assessment
    validation_score = len(strong_correlations) * 3 + len(moderate_correlations) * 1
    max_possible = len(correlations) * 3
    validation_percentage = (validation_score / max_possible) * 100
    
    report.extend([
        "## 🎯 Validation Summary",
        f"**Validation Strength:** {validation_percentage:.1f}% ({validation_score}/{max_possible} points)",
        f"- **Strong Correlations** (r > 0.6, p < 0.05): {len(strong_correlations)}",
        f"- **Moderate Correlations** (0.4 ≤ r ≤ 0.6, p < 0.05): {len(moderate_correlations)}",
        f"- **Weak/Non-significant** (r < 0.4 or p ≥ 0.05): {len(weak_correlations)}",
        ""
    ])
    
    # Overall conclusion
    if validation_percentage >= 70:
        conclusion = "✅ **STRONG VALIDATION**: YARA methodology shows strong correlation with established Lighthouse metrics."
    elif validation_percentage >= 50:
        conclusion = "⚠️ **MODERATE VALIDATION**: YARA shows reasonable correlation but needs calibration."
    else:
        conclusion = "❌ **WEAK VALIDATION**: YARA methodology needs significant revision."
    
    report.extend([
        f"### {conclusion}",
        ""
    ])
    
    # Detailed correlation analysis
    if strong_correlations:
        report.extend([
            "## ✅ Strong Correlations",
            ""
        ])
        
        for corr in strong_correlations:
            report.append(f"- **{corr['description']}**: r = {corr['correlation']:.3f} (p = {corr['p_value']:.3f}, n = {corr['sample_size']})")
        report.append("")
    
    if moderate_correlations:
        report.extend([
            "## ⚠️ Moderate Correlations", 
            ""
        ])
        
        for corr in moderate_correlations:
            report.append(f"- **{corr['description']}**: r = {corr['correlation']:.3f} (p = {corr['p_value']:.3f}, n = {corr['sample_size']})")
        report.append("")
    
    if weak_correlations:
        report.extend([
            "## ❌ Weak/Non-significant Correlations",
            ""
        ])
        
        for corr in weak_correlations:
            report.append(f"- **{corr['description']}**: r = {corr['correlation']:.3f} (p = {corr['p_value']:.3f}, n = {corr['sample_size']})")
        report.append("")
    
    # Site-by-site comparison
    report.extend([
        "## 🔍 Site-by-Site Analysis",
        ""
    ])
    
    # Combine and sort by YARA score
    combined = []
    for yara, lighthouse in zip(yara_scores, lighthouse_scores):
        combined.append({
            'url': yara.url,
            'yara_overall': yara.parseability_score,
            'yara_semantic': yara.semantic_structure,
            'yara_heading': yara.heading_hierarchy,
            'lighthouse_accessibility': lighthouse.accessibility,
            'lighthouse_seo': lighthouse.seo,
            'lighthouse_performance': lighthouse.performance,
            'failure_mode': yara.failure_mode
        })
    
    combined.sort(key=lambda x: x['yara_overall'], reverse=True)
    
    for site in combined:
        accessibility_match = "✅" if abs(site['yara_overall'] - site['lighthouse_accessibility']) < 20 else "❌"
        seo_match = "✅" if abs(site['yara_semantic'] - site['lighthouse_seo']) < 20 else "❌"
        
        report.extend([
            f"### {site['url']}",
            f"- **YARA Overall**: {site['yara_overall']:.1f}/100 ({site['failure_mode']})",
            f"- **YARA Semantic**: {site['yara_semantic']:.1f}/100 | **Lighthouse Accessibility**: {site['lighthouse_accessibility']:.1f}/100 {accessibility_match}",
            f"- **YARA Heading**: {site['yara_heading']:.1f}/100 | **Lighthouse SEO**: {site['lighthouse_seo']:.1f}/100 {seo_match}",
            f"- **Lighthouse Performance**: {site['lighthouse_performance']:.1f}/100",
            ""
        ])
    
    # Framework recommendation
    report.extend([
        "## 🚀 Framework Recommendation",
        ""
    ])
    
    if validation_percentage >= 70:
        report.extend([
            "**Recommendation**: YARA methodology is validated by Lighthouse correlation. Consider:",
            "- Fine-tuning YARA thresholds based on Lighthouse alignment",
            "- Using Lighthouse accessibility as validation benchmark",
            "- Hybrid scoring: YARA structure + Lighthouse accessibility"
        ])
    elif validation_percentage >= 50:
        report.extend([
            "**Recommendation**: Mixed validation suggests hybrid approach:",
            "- Use Lighthouse accessibility/SEO as foundation (70% weight)",
            "- Keep YARA's innovative content negotiation (20% weight)", 
            "- Add direct agent performance testing (10% weight)",
            "- Market as 'Agent-Ready Audit' rather than pure structural analysis"
        ])
    else:
        report.extend([
            "**Recommendation**: Weak correlation suggests framework pivot:",
            "- Replace YARA structural scoring with Lighthouse foundation",
            "- Preserve YARA's content negotiation detection as differentiator",
            "- Focus on actual agent performance correlation over HTML analysis",
            "- Position as evolution: 'YARA 2.0 - Beyond Structure to Agent Performance'"
        ])
    
    return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description="Compare YARA scores with Lighthouse metrics via PageSpeed Insights API")
    parser.add_argument("yara_results", help="Directory containing YARA evaluation results")
    parser.add_argument("--api-key", help="Google PageSpeed Insights API key (optional, increases rate limits)")
    parser.add_argument("--output", "-o", help="Save comparison report to file")
    parser.add_argument("--json-output", help="Save raw correlation data as JSON")
    
    args = parser.parse_args()
    
    try:
        # Run comparison
        comparison_data = run_lighthouse_yara_comparison(args.yara_results, args.api_key)
        
        # Generate report
        report = generate_lighthouse_comparison_report(comparison_data)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 Lighthouse comparison report saved to {args.output}")
        
        if args.json_output:
            # Prepare JSON-serializable data
            json_data = {
                'correlations': comparison_data['correlations'],
                'yara_scores': [
                    {
                        'url': score.url,
                        'parseability_score': score.parseability_score,
                        'semantic_structure': score.semantic_structure,
                        'heading_hierarchy': score.heading_hierarchy,
                        'content_density': score.content_density,
                        'rich_content': score.rich_content,
                        'boilerplate_resistance': score.boilerplate_resistance,
                        'failure_mode': score.failure_mode
                    }
                    for score in comparison_data['yara_scores']
                ],
                'lighthouse_scores': [
                    {
                        'url': score.url,
                        'accessibility': score.accessibility,
                        'seo': score.seo,
                        'best_practices': score.best_practices,
                        'performance': score.performance,
                        'pwa': score.pwa
                    }
                    for score in comparison_data['lighthouse_scores']
                ]
            }
            
            with open(args.json_output, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print(f"📄 Raw correlation data saved to {args.json_output}")
        
        print(report)
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())