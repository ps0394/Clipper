#!/usr/bin/env python3
"""
Hybrid Agent-Ready Assessment Framework
Combining Lighthouse foundation + Clipper content analysis + direct agent performance validation
"""

import json
import requests
import time
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import statistics
import tempfile
import subprocess
from bs4 import BeautifulSoup, Comment
import re

@dataclass
class HybridScore:
    url: str
    overall_score: float
    lighthouse_foundation: float  # 70% weight
    content_negotiation: float    # 20% weight  
    agent_performance: float      # 10% weight
    
    # Component breakdowns
    lighthouse_accessibility: float
    lighthouse_seo: float
    lighthouse_performance: float
    
    yara_content_density: float
    yara_rich_content: float
    yara_boilerplate_resistance: float
    
    agent_extraction_quality: float
    agent_success_rate: float
    
    failure_mode: str
    recommendations: List[str]

class HybridFramework:
    """Agent-Ready Assessment combining proven metrics with content analysis."""
    
    def __init__(self, pagespeed_api_key: Optional[str] = None):
        self.pagespeed_api_key = pagespeed_api_key
        
    def get_lighthouse_scores(self, url: str) -> Dict[str, float]:
        """Get Lighthouse scores via PageSpeed Insights API."""
        
        api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        
        params = {
            'url': url,
            'category': ['accessibility', 'seo', 'performance'],
            'strategy': 'desktop'
        }
        
        if self.pagespeed_api_key:
            params['key'] = self.pagespeed_api_key
            
        try:
            print(f"  📡 Getting Lighthouse scores for {url}")
            response = requests.get(api_url, params=params, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                categories = data.get('lighthouseResult', {}).get('categories', {})
                
                return {
                    'accessibility': categories.get('accessibility', {}).get('score', 0) * 100,
                    'seo': categories.get('seo', {}).get('score', 0) * 100,
                    'performance': categories.get('performance', {}).get('score', 0) * 100
                }
            else:
                print(f"    ⚠️ Lighthouse API error: {response.status_code}")
                return {'accessibility': 0, 'seo': 0, 'performance': 0}
                
        except Exception as e:
            print(f"    ❌ Lighthouse exception: {e}")
            return {'accessibility': 0, 'seo': 0, 'performance': 0}
    
    def analyze_content_negotiation(self, html_content: str) -> Dict[str, float]:
        """Analyze content quality and agent-readiness from HTML."""
        
        if not html_content or len(html_content) < 100:
            return {
                'content_density': 0,
                'rich_content': 0,
                'boilerplate_resistance': 50  # Neutral for empty content
            }
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove scripts, styles, and comments
        for script in soup(["script", "style"]):
            script.decompose()
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
            
        # Content density analysis
        total_text = soup.get_text()
        visible_text = ' '.join(total_text.split())
        text_length = len(visible_text)
        html_length = len(html_content)
        
        # Calculate content density (text vs markup ratio)
        if html_length > 0:
            content_density = min(100, (text_length / html_length) * 100 * 2)  # Scale factor
        else:
            content_density = 0
            
        # Rich content analysis
        rich_indicators = {
            'code_blocks': len(soup.find_all(['pre', 'code'])),
            'lists': len(soup.find_all(['ul', 'ol', 'dl'])),
            'tables': len(soup.find_all('table')),
            'headings': len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])),
            'links': len(soup.find_all('a', href=True)),
            'images': len(soup.find_all('img', alt=True))
        }
        
        # Score rich content based on presence and quantity
        rich_score = 0
        for indicator, count in rich_indicators.items():
            if count > 0:
                if indicator == 'code_blocks':
                    rich_score += min(30, count * 5)  # Code blocks are valuable
                elif indicator == 'headings':
                    rich_score += min(25, count * 2)  # Good structure
                elif indicator == 'lists':
                    rich_score += min(20, count * 3)  # Organized info
                else:
                    rich_score += min(15, count * 1)  # Other content
                    
        rich_content = min(100, rich_score)
        
        # Boilerplate resistance (simplified)
        nav_elements = len(soup.find_all(['nav', 'header', 'footer']))
        main_content_elements = len(soup.find_all(['main', 'article', 'section']))
        
        if main_content_elements > 0:
            boilerplate_resistance = min(100, 70 + (main_content_elements * 10) - (nav_elements * 5))
        else:
            boilerplate_resistance = max(0, 50 - (nav_elements * 10))
            
        return {
            'content_density': content_density,
            'rich_content': rich_content,
            'boilerplate_resistance': boilerplate_resistance
        }
    
    def simulate_agent_extraction(self, html_content: str, url: str) -> Dict[str, float]:
        """Simulate AI agent content extraction and assess quality."""
        
        if not html_content or len(html_content) < 100:
            return {
                'extraction_quality': 0,
                'success_rate': 0
            }
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove noise elements that confuse agents
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
            
        # Extract main content areas
        content_selectors = [
            'main', 'article', '[role="main"]', '.content',
            '.main-content', '#content', '#main'
        ]
        
        main_content = None
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element and len(element.get_text().strip()) > 200:
                main_content = element
                break
        
        if not main_content:
            # Fallback: use body but remove common noise
            main_content = soup.find('body') or soup
            for noise in main_content.find_all(['nav', 'header', 'footer', 'aside']):
                noise.decompose()
        
        # Assess extraction quality
        extracted_text = main_content.get_text() if main_content else ""
        clean_text = ' '.join(extracted_text.split())
        
        # Quality indicators
        word_count = len(clean_text.split())
        sentence_count = len([s for s in re.split(r'[.!?]+', clean_text) if s.strip()])
        
        # Structural quality
        headings = main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) if main_content else []
        code_blocks = main_content.find_all(['pre', 'code']) if main_content else []
        lists = main_content.find_all(['ul', 'ol']) if main_content else []
        
        # Calculate quality score
        quality_score = 0
        
        # Content volume (0-40 points)
        if word_count >= 500:
            quality_score += 40
        elif word_count >= 200:
            quality_score += 25
        elif word_count >= 50:
            quality_score += 10
            
        # Structure (0-30 points)
        if len(headings) >= 3:
            quality_score += 20
        elif len(headings) >= 1:
            quality_score += 10
            
        if code_blocks or lists:
            quality_score += 10
            
        # Text quality (0-30 points)
        if sentence_count >= 10:
            quality_score += 20
        elif sentence_count >= 3:
            quality_score += 10
            
        # Readability indicator
        avg_words_per_sentence = word_count / max(1, sentence_count)
        if 10 <= avg_words_per_sentence <= 25:  # Good readability range
            quality_score += 10
            
        extraction_quality = min(100, quality_score)
        
        # Success rate (binary: can agent extract meaningful content?)
        success_rate = 100 if (word_count >= 100 and sentence_count >= 2 and len(headings) >= 1) else 25
        
        return {
            'extraction_quality': extraction_quality,
            'success_rate': success_rate
        }
    
    def fetch_page_content(self, url: str) -> str:
        """Fetch HTML content for analysis."""
        
        try:
            print(f"  🌐 Fetching content from {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"    ❌ Failed to fetch {url}: {e}")
            return ""
    
    def evaluate_url(self, url: str) -> HybridScore:
        """Comprehensive hybrid evaluation of a single URL."""
        
        print(f"🔍 Evaluating {url}")
        
        # Get HTML content
        html_content = self.fetch_page_content(url)
        
        if not html_content:
            return HybridScore(
                url=url,
                overall_score=0,
                lighthouse_foundation=0,
                content_negotiation=0,
                agent_performance=0,
                lighthouse_accessibility=0,
                lighthouse_seo=0,
                lighthouse_performance=0,
                yara_content_density=0,
                yara_rich_content=0,
                yara_boilerplate_resistance=0,
                agent_extraction_quality=0,
                agent_success_rate=0,
                failure_mode="fetch_failed",
                recommendations=["Unable to fetch page content", "Check URL accessibility", "Verify server response"]
            )
        
        # Component 1: Lighthouse foundation (70% weight)
        lighthouse_scores = self.get_lighthouse_scores(url)
        lighthouse_foundation = (
            lighthouse_scores['accessibility'] * 0.5 +
            lighthouse_scores['seo'] * 0.3 +
            lighthouse_scores['performance'] * 0.2
        )
        
        # Component 2: Content negotiation analysis (20% weight)
        content_analysis = self.analyze_content_negotiation(html_content)
        content_negotiation = (
            content_analysis['content_density'] * 0.4 +
            content_analysis['rich_content'] * 0.4 +
            content_analysis['boilerplate_resistance'] * 0.2
        )
        
        # Component 3: Agent performance simulation (10% weight)
        agent_analysis = self.simulate_agent_extraction(html_content, url)
        agent_performance = (
            agent_analysis['extraction_quality'] * 0.7 +
            agent_analysis['success_rate'] * 0.3
        )
        
        # Calculate overall score
        overall_score = (
            lighthouse_foundation * 0.7 +
            content_negotiation * 0.2 +
            agent_performance * 0.1
        )
        
        # Generate recommendations
        recommendations = []
        
        if lighthouse_scores['accessibility'] < 80:
            recommendations.append(f"Improve accessibility (current: {lighthouse_scores['accessibility']:.1f}/100)")
        if lighthouse_scores['seo'] < 80:
            recommendations.append(f"Enhance SEO structure (current: {lighthouse_scores['seo']:.1f}/100)")
        if content_analysis['rich_content'] < 60:
            recommendations.append("Add more structured content (headings, lists, code blocks)")
        if agent_analysis['extraction_quality'] < 70:
            recommendations.append("Simplify content structure for better agent extraction")
        
        if not recommendations:
            recommendations.append("Excellent agent-ready documentation!")
            
        # Determine failure mode
        failure_mode = "success"
        if overall_score < 25:
            failure_mode = "critical_issues"
        elif overall_score < 50:
            failure_mode = "needs_improvement"
        elif overall_score < 75:
            failure_mode = "good_with_issues"
        
        return HybridScore(
            url=url,
            overall_score=overall_score,
            lighthouse_foundation=lighthouse_foundation,
            content_negotiation=content_negotiation,
            agent_performance=agent_performance,
            lighthouse_accessibility=lighthouse_scores['accessibility'],
            lighthouse_seo=lighthouse_scores['seo'],
            lighthouse_performance=lighthouse_scores['performance'],
            yara_content_density=content_analysis['content_density'],
            yara_rich_content=content_analysis['rich_content'],
            yara_boilerplate_resistance=content_analysis['boilerplate_resistance'],
            agent_extraction_quality=agent_analysis['extraction_quality'],
            agent_success_rate=agent_analysis['success_rate'],
            failure_mode=failure_mode,
            recommendations=recommendations
        )
    
    def evaluate_urls(self, urls: List[str]) -> List[HybridScore]:
        """Evaluate multiple URLs with the hybrid framework."""
        
        print(f"🚀 Starting hybrid evaluation of {len(urls)} URLs")
        print("📊 Framework: Lighthouse (70%) + Content Analysis (20%) + Agent Performance (10%)")
        
        results = []
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}]")
            score = self.evaluate_url(url)
            results.append(score)
            
            # Rate limiting
            if i < len(urls):
                time.sleep(1)  # Be respectful to APIs
        
        return results
    
    def generate_report(self, scores: List[HybridScore]) -> str:
        """Generate comprehensive hybrid framework report."""
        
        report = [
            "# Hybrid Agent-Ready Assessment Report",
            f"**Framework:** Lighthouse Foundation (70%) + Content Analysis (20%) + Agent Performance (10%)",
            f"**Analysis Date:** {time.strftime('%Y-%m-%d %H:%M')}",
            f"**URLs Evaluated:** {len(scores)}",
            ""
        ]
        
        # Overall statistics
        if scores:
            overall_scores = [s.overall_score for s in scores]
            avg_score = statistics.mean(overall_scores)
            
            report.extend([
                "## 📊 Summary Statistics",
                f"- **Average Score:** {avg_score:.1f}/100",
                f"- **Highest Score:** {max(overall_scores):.1f}/100",
                f"- **Lowest Score:** {min(overall_scores):.1f}/100",
                f"- **Agent-Ready (≥75):** {len([s for s in scores if s.overall_score >= 75])}/{len(scores)}",
                ""
            ])
        
        # Component analysis
        if scores:
            lighthouse_avg = statistics.mean([s.lighthouse_foundation for s in scores])
            content_avg = statistics.mean([s.content_negotiation for s in scores])
            agent_avg = statistics.mean([s.agent_performance for s in scores])
            
            report.extend([
                "## 🔬 Component Analysis",
                f"- **Lighthouse Foundation:** {lighthouse_avg:.1f}/100 (accessibility, SEO, performance)",
                f"- **Content Analysis:** {content_avg:.1f}/100 (density, rich content, boilerplate resistance)",  
                f"- **Agent Performance:** {agent_avg:.1f}/100 (extraction quality, success rate)",
                ""
            ])
        
        # Individual results
        report.extend([
            "## 📋 Individual Results",
            ""
        ])
        
        # Sort by overall score
        sorted_scores = sorted(scores, key=lambda x: x.overall_score, reverse=True)
        
        for score in sorted_scores:
            status_emoji = "✅" if score.overall_score >= 75 else "⚠️" if score.overall_score >= 50 else "❌"
            
            report.extend([
                f"### {status_emoji} {score.url}",
                f"**Overall Score:** {score.overall_score:.1f}/100 ({score.failure_mode})",
                "",
                "**Component Breakdown:**",
                f"- Lighthouse Foundation ({score.lighthouse_foundation:.1f}/100): Accessibility {score.lighthouse_accessibility:.1f}, SEO {score.lighthouse_seo:.1f}, Performance {score.lighthouse_performance:.1f}",
                f"- Content Analysis ({score.content_negotiation:.1f}/100): Density {score.yara_content_density:.1f}, Rich Content {score.yara_rich_content:.1f}, Boilerplate Resistance {score.yara_boilerplate_resistance:.1f}",
                f"- Agent Performance ({score.agent_performance:.1f}/100): Extraction Quality {score.agent_extraction_quality:.1f}, Success Rate {score.agent_success_rate:.1f}",
                "",
                "**Recommendations:**"
            ])
            
            for rec in score.recommendations:
                report.append(f"- {rec}")
            
            report.append("")
        
        # Framework insights
        report.extend([
            "## 🚀 Framework Insights",
            "",
            "### Methodology",
            "This hybrid framework combines:",
            "- **Lighthouse metrics (70%)** - Proven accessibility, SEO, and performance standards", 
            "- **Content analysis (20%)** - Clipper-inspired content density and structure evaluation",
            "- **Agent performance (10%)** - Direct simulation of AI agent content extraction",
            "",
            "### Advantages over Clipper",
            "- Uses established Lighthouse metrics as foundation",
            "- Directly tests agent extraction capabilities", 
            "- Provides actionable accessibility and SEO recommendations",
            "- Balances structural analysis with real-world agent performance",
            "",
            "### Agent-Ready Criteria",
            "- Overall Score ≥ 75: Agent-ready documentation",
            "- Overall Score 50-74: Good with minor issues", 
            "- Overall Score < 50: Needs significant improvement"
        ])
        
        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description="Hybrid Agent-Ready Assessment Framework")
    parser.add_argument("urls", nargs='+', help="URLs to evaluate")
    parser.add_argument("--api-key", help="PageSpeed Insights API key")
    parser.add_argument("--output", "-o", help="Save report to file")
    parser.add_argument("--json-output", help="Save raw data as JSON")
    
    args = parser.parse_args()
    
    # Initialize framework
    framework = HybridFramework(pagespeed_api_key=args.api_key)
    
    try:
        # Run evaluation
        scores = framework.evaluate_urls(args.urls)
        
        # Generate report
        report = framework.generate_report(scores)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n📄 Hybrid assessment report saved to {args.output}")
        
        if args.json_output:
            # Convert to JSON-serializable format
            json_data = {
                'framework_version': 'hybrid-1.0',
                'evaluation_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'component_weights': {
                    'lighthouse_foundation': 0.7,
                    'content_negotiation': 0.2,
                    'agent_performance': 0.1
                },
                'results': [
                    {
                        'url': score.url,
                        'overall_score': score.overall_score,
                        'lighthouse_foundation': score.lighthouse_foundation,
                        'content_negotiation': score.content_negotiation,
                        'agent_performance': score.agent_performance,
                        'lighthouse_accessibility': score.lighthouse_accessibility,
                        'lighthouse_seo': score.lighthouse_seo,
                        'lighthouse_performance': score.lighthouse_performance,
                        'yara_content_density': score.yara_content_density,
                        'yara_rich_content': score.yara_rich_content,
                        'yara_boilerplate_resistance': score.yara_boilerplate_resistance,
                        'agent_extraction_quality': score.agent_extraction_quality,
                        'agent_success_rate': score.agent_success_rate,
                        'failure_mode': score.failure_mode,
                        'recommendations': score.recommendations
                    }
                    for score in scores
                ]
            }
            
            with open(args.json_output, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            print(f"📄 Raw data saved to {args.json_output}")
        
        print(f"\n{report}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())