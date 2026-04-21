#!/usr/bin/env python3
"""
Extract HTML examples for presentation materials
Usage: python extract-html-evidence.py results/ --examples 5
"""

import json
import argparse
from pathlib import Path

def extract_html_evidence(results_dir, num_examples=5):
    """Extract HTML examples for good/bad scoring patterns"""
    
    # Load the scores and URL mapping
    scores_file = Path(results_dir) / 'report_scores.json'
    crawl_file = Path(results_dir) / 'crawl_results.json'
    parse_file = Path(results_dir) / 'report_parse.json'
    
    with open(scores_file) as f:
        scores = json.load(f)
    with open(crawl_file) as f:
        crawl_data = json.load(f)
    with open(parse_file) as f:
        parse_data = json.load(f)
    
    # Create URL mapping
    url_mapping = {item['html_path']: item['url'] for item in crawl_data}
    
    # Sort by score for examples
    scored_pages = []
    for i, score_data in enumerate(scores):
        if i < len(parse_data):
            html_file = parse_data[i]['html_path']
            url = url_mapping.get(html_file, 'Unknown URL')
            
            scored_pages.append({
                'url': url,
                'html_file': html_file,
                'score': score_data['parseability_score'],
                'failure_mode': score_data['failure_mode'],
                'evidence': parse_data[i]['evidence']
            })
    
    # Sort by score (best and worst examples)
    scored_pages.sort(key=lambda x: x['score'])
    
    print("🎯 **HTML EVIDENCE FOR PRESENTATION**\n")
    
    # Best examples (high scores)
    best_examples = scored_pages[-num_examples//2:]
    print("✅ **HIGH SCORING EXAMPLES** (Use these as positive patterns):")
    for page in best_examples:
        print(f"\n**Score: {page['score']:.1f}/100** - {page['url']}")
        print(f"HTML File: {page['html_file']}")
        print(f"Why it scored well:")
        
        if page['evidence']['semantic_elements']['main_count'] > 0:
            print(f"  ✅ Has <main> element ({page['evidence']['semantic_elements']['main_count']} found)")
        if page['evidence']['semantic_elements']['article_count'] > 0:
            print(f"  ✅ Has <article> element ({page['evidence']['semantic_elements']['article_count']} found)")
            
        headings = page['evidence']['heading_structure']
        if headings:
            print(f"  ✅ Good heading structure ({len(headings)} headings)")
            print(f"     Example: H{headings[0]['level']}: '{headings[0]['text'][:50]}...'")
    
    print("\n" + "="*80 + "\n")
    
    # Worst examples (low scores) 
    worst_examples = scored_pages[:num_examples//2]
    print("❌ **LOW SCORING EXAMPLES** (Issues to fix):")
    for page in worst_examples:
        print(f"\n**Score: {page['score']:.1f}/100** - {page['url']}")
        print(f"HTML File: {page['html_file']}")
        print(f"Issues found:")
        
        if page['evidence']['semantic_elements']['main_count'] == 0:
            print(f"  ❌ Missing <main> element")
        if page['evidence']['semantic_elements']['article_count'] == 0:
            print(f"  ❌ Missing <article> element")
            
        # Check for heading issues
        headings = page['evidence']['heading_structure']
        if len(headings) < 3:
            print(f"  ❌ Poor heading structure (only {len(headings)} headings)")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract HTML evidence for presentations')
    parser.add_argument('results_dir', help='Clipper results directory')
    parser.add_argument('--examples', type=int, default=6, help='Number of examples to show')
    
    args = parser.parse_args()
    extract_html_evidence(args.results_dir, args.examples)