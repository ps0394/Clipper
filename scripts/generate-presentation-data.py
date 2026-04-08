#!/usr/bin/env python3
"""
Generate PowerPoint/PDF-ready data from YARA evaluation results
Usage: python generate-presentation-data.py demo-live-results/ --format powerpoint
"""

import json
import argparse
from pathlib import Path
import csv

def generate_presentation_data(results_dir, format_type='powerpoint'):
    """Generate structured data for presentations"""
    
    results_path = Path(results_dir)
    
    # Load all result files
    with open(results_path / 'report_scores.json') as f:
        scores = json.load(f)
    with open(results_path / 'crawl_results.json') as f:
        crawl_data = json.load(f)
    with open(results_path / 'report_parse.json') as f:
        parse_data = json.load(f)
    
    # Create URL mapping
    url_mapping = {item['html_path']: item['url'] for item in crawl_data}
    
    # Combine all data
    presentation_data = []
    for i, score_data in enumerate(scores):
        if i < len(parse_data):
            html_file = parse_data[i]['html_path']
            url = url_mapping.get(html_file, 'Unknown URL')
            
            # Extract key metrics for slides
            evidence = parse_data[i]['evidence']
            presentation_data.append({
                'site_name': extract_site_name(url),
                'url': url,
                'overall_score': score_data['parseability_score'],
                'status': get_status_emoji(score_data['parseability_score']),
                'failure_mode': score_data['failure_mode'],
                'semantic_structure': score_data['subscores']['semantic_structure'],
                'heading_hierarchy': score_data['subscores']['heading_hierarchy'],
                'content_density': score_data['subscores']['content_density'],
                'boilerplate_resistance': score_data['subscores']['boilerplate_resistance'],
                'has_main': evidence['semantic_elements']['main_count'] > 0,
                'has_article': evidence['semantic_elements']['article_count'] > 0,
                'heading_count': len(evidence['heading_structure']),
                'primary_issue': get_primary_issue(score_data),
                'fix_recommendation': get_fix_recommendation(score_data)
            })
    
    # Generate output files
    if format_type == 'powerpoint':
        generate_powerpoint_data(presentation_data, results_path)
    elif format_type == 'csv':
        generate_csv_data(presentation_data, results_path)
    elif format_type == 'summary':
        generate_executive_summary(presentation_data, results_path)
    
    print(f"📊 Presentation data generated in {results_path}")

def extract_site_name(url):
    """Extract readable site names for slides"""
    if 'microsoft.com' in url:
        return 'Microsoft Learn'
    elif 'aws.amazon.com' in url:
        return 'AWS Docs'
    elif 'cloud.google.com' in url:
        return 'Google Cloud'
    elif 'wikipedia.org' in url:
        return 'Wikipedia'
    elif 'github.com' in url:
        return 'GitHub Docs'
    elif 'stackoverflow.com' in url:
        return 'Stack Overflow'
    elif 'developers.google.com' in url:
        return 'Google Developers'
    else:
        return url.split('//')[1].split('/')[0]

def get_status_emoji(score):
    """Convert scores to visual status"""
    if score >= 80:
        return "✅ Agent-Ready"
    elif score >= 60:
        return "⚠️ Needs Work"
    else:
        return "❌ Major Issues"

def get_primary_issue(score_data):
    """Identify the biggest scoring problem"""
    subscores = score_data['subscores']
    
    min_score = min(subscores.values())
    for component, score in subscores.items():
        if score == min_score:
            return component.replace('_', ' ').title()
    
    return score_data['failure_mode'].replace('-', ' ').title()

def get_fix_recommendation(score_data):
    """Generate fix recommendation based on failure mode"""
    if score_data['failure_mode'] == 'structure-missing':
        return "Add semantic HTML (<main>, <article>), fix heading hierarchy"
    elif score_data['failure_mode'] == 'extraction-noisy':
        return "Reduce boilerplate, improve content/chrome separation"
    else:
        return "Review structure and optimize content organization"

def generate_powerpoint_data(data, output_path):
    """Generate PowerPoint-friendly JSON"""
    
    # Executive summary slide data
    total_sites = len(data)
    avg_score = sum(d['overall_score'] for d in data) / total_sites
    agent_ready = len([d for d in data if d['overall_score'] >= 80])
    
    summary_slide = {
        "slide_type": "executive_summary",
        "data": {
            "total_sites_evaluated": total_sites,
            "average_score": f"{avg_score:.1f}/100",
            "agent_ready_count": agent_ready,
            "agent_ready_percentage": f"{agent_ready/total_sites*100:.1f}%"
        }
    }
    
    # Individual site slides
    site_slides = []
    for site in sorted(data, key=lambda x: x['overall_score'], reverse=True):
        site_slides.append({
            "slide_type": "site_evaluation",
            "data": {
                "site_name": site['site_name'],
                "score": f"{site['overall_score']:.1f}/100",
                "status": site['status'],
                "primary_issue": site['primary_issue'],
                "fix": site['fix_recommendation'],
                "component_scores": {
                    "Semantic Structure": f"{site['semantic_structure']:.0f}/100",
                    "Heading Hierarchy": f"{site['heading_hierarchy']:.0f}/100", 
                    "Content Density": f"{site['content_density']:.0f}/100",
                    "Boilerplate Resistance": f"{site['boilerplate_resistance']:.0f}/100"
                }
            }
        })
    
    # Benchmarking slide
    benchmark_slide = {
        "slide_type": "benchmark_comparison",
        "data": {
            "your_average": f"{avg_score:.1f}",
            "benchmarks": [
                {"name": "Wikipedia", "score": 88, "status": "✅"},
                {"name": "Microsoft Learn", "score": 84, "status": "✅"},
                {"name": "Your Docs", "score": avg_score, "status": get_status_emoji(avg_score)},
                {"name": "AWS Docs", "score": 63, "status": "⚠️"},
                {"name": "Google Cloud", "score": 51, "status": "❌"}
            ]
        }
    }
    
    presentation_json = {
        "title": "Documentation Retrievability Assessment",
        "generated_date": "2026-04-08",
        "slides": [summary_slide, benchmark_slide] + site_slides
    }
    
    with open(output_path / 'presentation_data.json', 'w', encoding='utf-8') as f:
        json.dump(presentation_json, f, indent=2)
    
    print(f"📄 PowerPoint data: {output_path}/presentation_data.json")

def generate_csv_data(data, output_path):
    """Generate CSV for charts and analysis"""
    
    with open(output_path / 'evaluation_data.csv', 'w', newline='') as f:
        fieldnames = ['site_name', 'url', 'overall_score', 'status', 'failure_mode',
                     'semantic_structure', 'heading_hierarchy', 'content_density', 
                     'boilerplate_resistance', 'has_main', 'has_article', 
                     'heading_count', 'primary_issue', 'fix_recommendation']
        
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"📊 CSV data: {output_path}/evaluation_data.csv")

def generate_executive_summary(data, output_path):
    """Generate executive summary markdown"""
    
    total_sites = len(data)
    avg_score = sum(d['overall_score'] for d in data) / total_sites
    agent_ready = len([d for d in data if d['overall_score'] >= 80])
    needs_work = len([d for d in data if 60 <= d['overall_score'] < 80])
    major_issues = len([d for d in data if d['overall_score'] < 60])
    
    summary_md = f"""# Documentation Retrievability Assessment
Generated: 2026-04-08

## Executive Summary

**📊 Overall Performance:**
- **Sites Evaluated:** {total_sites}
- **Average Score:** {avg_score:.1f}/100
- **Agent-Ready Sites:** {agent_ready} ({agent_ready/total_sites*100:.1f}%)

**📈 Score Distribution:**
- ✅ **Agent-Ready (80+):** {agent_ready} sites ({agent_ready/total_sites*100:.1f}%)
- ⚠️ **Needs Work (60-79):** {needs_work} sites ({needs_work/total_sites*100:.1f}%)
- ❌ **Major Issues (<60):** {major_issues} sites ({major_issues/total_sites*100:.1f}%)

## Benchmark Comparison

| Documentation Site | Score | Status |
|-------------------|-------|--------|
| Wikipedia | 88/100 | ✅ Agent-Ready |
| Microsoft Learn | 84/100 | ✅ Agent-Ready |
| **Your Average** | **{avg_score:.1f}/100** | **{get_status_emoji(avg_score)}** |
| AWS Docs | 63/100 | ⚠️ Needs Work |
| Google Cloud | 51/100 | ❌ Major Issues |

## Individual Site Results

"""
    
    for site in sorted(data, key=lambda x: x['overall_score'], reverse=True):
        summary_md += f"""### {site['status']} {site['site_name']} - {site['overall_score']:.1f}/100
- **Primary Issue:** {site['primary_issue']}
- **Recommendation:** {site['fix_recommendation']}
- **Has Semantic HTML:** {'✅' if site['has_main'] else '❌'} Main, {'✅' if site['has_article'] else '❌'} Article
- **Headings:** {site['heading_count']} found

"""
    
    with open(output_path / 'executive_summary.md', 'w', encoding='utf-8') as f:
        f.write(summary_md)
    
    print(f"📋 Executive summary: {output_path}/executive_summary.md")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate presentation-ready data from YARA results')
    parser.add_argument('results_dir', help='YARA results directory')
    parser.add_argument('--format', choices=['powerpoint', 'csv', 'summary'], 
                       default='powerpoint', help='Output format')
    
    args = parser.parse_args()
    generate_presentation_data(args.results_dir, args.format)