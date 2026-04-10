"""Hybrid scoring engine combining Lighthouse + Content Analysis + Agent Performance."""

import json
import requests
import time
from pathlib import Path
from typing import Dict, List, Optional
from bs4 import BeautifulSoup, Comment
import re
from .schemas import ScoreResult


class HybridScorer:
    """YARA 2.0 hybrid scoring engine."""
    
    def __init__(self, pagespeed_api_key: Optional[str] = None):
        self.pagespeed_api_key = pagespeed_api_key
        
    def score_parse_results(self, parse_file: str, output_file: str) -> None:
        """Score parse results using hybrid methodology.
        
        Args:
            parse_file: JSON file with parse results
            output_file: JSON file to save hybrid score results
        """
        parse_path = Path(parse_file)
        if not parse_path.exists():
            raise FileNotFoundError(f"Parse file not found: {parse_file}")
        
        with open(parse_path, 'r', encoding='utf-8') as f:
            parse_results_data = json.load(f)
        
        # Load URLs from crawl results for Lighthouse analysis
        urls = self._load_urls_from_crawl_results(parse_path)
        
        score_results = []
        
        for i, parse_data in enumerate(parse_results_data):
            print(f"Hybrid scoring: {parse_data['html_path']}")
            
            # Get URL for this parse result
            url = urls[i] if i < len(urls) else None
            
            score_result = self._score_parse_result_hybrid(parse_data, url)
            score_results.append(score_result)
        
        # Save hybrid score results
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([result.to_dict() for result in score_results], f, indent=2)
        
        print(f"Hybrid scored {len(score_results)} results, saved to {output_file}")
    
    def _load_urls_from_crawl_results(self, parse_path: Path) -> List[str]:
        """Load URLs from crawl_results.json for Lighthouse analysis."""
        
        # Try different locations for crawl_results.json
        possible_locations = [
            parse_path.parent / "crawl_results.json",
            parse_path.parent / "snapshots" / "crawl_results.json",
            parse_path.parent.parent / "crawl_results.json"
        ]
        
        for crawl_file in possible_locations:
            if crawl_file.exists():
                try:
                    with open(crawl_file, 'r', encoding='utf-8') as f:
                        crawl_data = json.load(f)
                    return [item['url'] for item in crawl_data]
                except Exception as e:
                    print(f"Warning: Could not load URLs from {crawl_file}: {e}")
                    continue
        
        print("Warning: Could not find crawl_results.json - Lighthouse analysis disabled")
        return []
    
    def _score_parse_result_hybrid(self, parse_data: Dict, url: Optional[str]) -> ScoreResult:
        """Score using YARA 2.0 hybrid methodology.
        
        Args:
            parse_data: Dictionary containing parse result data
            url: URL for Lighthouse analysis (if available)
            
        Returns:
            ScoreResult with hybrid scores and enhanced failure mode
        """
        signals = parse_data['signals']
        evidence = parse_data['evidence']
        
        # Component 1: Lighthouse Foundation (70% weight)
        lighthouse_scores = self._get_lighthouse_scores(url) if url else {'accessibility': 0, 'seo': 0, 'performance': 0}
        lighthouse_foundation = (
            lighthouse_scores['accessibility'] * 0.5 +
            lighthouse_scores['seo'] * 0.3 +
            lighthouse_scores['performance'] * 0.2
        )
        
        # Component 2: Content Analysis (20% weight) - Enhanced YARA analysis
        content_subscores = self._calculate_content_subscores(signals, evidence, parse_data)
        content_analysis = (
            content_subscores['content_density'] * 0.4 +
            content_subscores['rich_content'] * 0.4 +
            content_subscores['boilerplate_resistance'] * 0.2
        )
        
        # Component 3: Agent Performance (10% weight) - Simulated extraction
        agent_scores = self._simulate_agent_performance(parse_data)
        agent_performance = (
            agent_scores['extraction_quality'] * 0.7 +
            agent_scores['success_rate'] * 0.3
        )
        
        # Calculate hybrid overall score
        hybrid_score = (
            lighthouse_foundation * 0.7 +
            content_analysis * 0.2 +
            agent_performance * 0.1
        )
        
        # Enhanced subscores including hybrid components
        hybrid_subscores = {
            # Core YARA subscores
            'semantic_structure': content_subscores['semantic_structure'],
            'heading_hierarchy': content_subscores['heading_hierarchy'], 
            'content_density': content_subscores['content_density'],
            'rich_content': content_subscores['rich_content'],
            'boilerplate_resistance': content_subscores['boilerplate_resistance'],
            
            # New hybrid components
            'lighthouse_foundation': lighthouse_foundation,
            'lighthouse_accessibility': lighthouse_scores['accessibility'],
            'lighthouse_seo': lighthouse_scores['seo'],
            'lighthouse_performance': lighthouse_scores['performance'],
            'content_analysis': content_analysis,
            'agent_performance': agent_performance,
            'agent_extraction_quality': agent_scores['extraction_quality'],
            'agent_success_rate': agent_scores['success_rate']
        }
        
        # Enhanced failure mode classification
        failure_mode = self._classify_hybrid_failure_mode(
            hybrid_score, lighthouse_scores, content_subscores, agent_scores
        )
        
        # Enhanced evidence references
        evidence_refs = self._gather_hybrid_evidence(signals, evidence, lighthouse_scores, agent_scores)
        
        return ScoreResult(
            parseability_score=hybrid_score,
            failure_mode=failure_mode,
            subscores=hybrid_subscores,
            evidence_references=evidence_refs
        )
    
    def _get_lighthouse_scores(self, url: str) -> Dict[str, float]:
        """Get Lighthouse scores via PageSpeed Insights API."""
        
        if not url:
            raise ValueError("[ERROR] URL required for Lighthouse analysis")
        
        if not self.pagespeed_api_key:
            raise ValueError(
                "[ERROR] LIGHTHOUSE UNAVAILABLE, YARA CANNOT RUN\n"
                "\n"
                "PageSpeed Insights API key is required for YARA 2.0 hybrid scoring.\n"
                "Set PAGESPEED_API_KEY environment variable or pass --api-key parameter."
            )
            
        api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        
        params = {
            'url': url,
            'category': ['accessibility', 'seo', 'performance'],
            'strategy': 'desktop',
            'key': self.pagespeed_api_key
        }
            
        try:
            print(f"  📡 Getting Lighthouse scores...")
            response = requests.get(api_url, params=params, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                categories = data.get('lighthouseResult', {}).get('categories', {})
                
                return {
                    'accessibility': categories.get('accessibility', {}).get('score', 0) * 100,
                    'seo': categories.get('seo', {}).get('score', 0) * 100,
                    'performance': categories.get('performance', {}).get('score', 0) * 100
                }
            elif response.status_code == 429:
                raise ValueError(
                    f"[ERROR] LIGHTHOUSE API RATE LIMITED (HTTP {response.status_code})\n"
                    "\n"
                    "PageSpeed Insights API quota exceeded. Please:\n"
                    "  • Wait and try again later\n"
                    "  • Check your API key quota at: https://console.developers.google.com/\n"
                    "  • Consider upgrading your API quota if needed"
                )
            else:
                raise ValueError(
                    f"[ERROR] LIGHTHOUSE API ERROR (HTTP {response.status_code})\n"
                    "\n"
                    f"PageSpeed Insights API returned error {response.status_code}.\n"
                    "Please check your API key and try again.\n"
                    f"Response: {response.text[:200]}"
                )
                
        except requests.exceptions.RequestException as e:
            raise ValueError(
                f"[ERROR] LIGHTHOUSE API CONNECTION FAILED\n"
                "\n"
                f"Could not connect to PageSpeed Insights API: {e}\n"
                "Please check your internet connection and try again."
            )
    
    def _calculate_content_subscores(self, signals: Dict, evidence: Dict, parse_data: Dict) -> Dict[str, float]:
        """Calculate enhanced content analysis subscores."""
        
        subscores = {}
        
        # Enhanced semantic structure (using existing YARA logic)
        semantic_score = 0.0
        if signals['has_main_element']:
            semantic_score += 60.0
        if signals['has_article_element']:
            semantic_score += 40.0
        subscores['semantic_structure'] = min(semantic_score, 100.0)
        
        # Enhanced heading hierarchy
        if signals['heading_hierarchy_valid']:
            hierarchy_score = 100.0
        else:
            heading_count = len(evidence.get('heading_structure', []))
            if heading_count > 0:
                hierarchy_score = 30.0
            else:
                hierarchy_score = 0.0
        subscores['heading_hierarchy'] = hierarchy_score
        
        # Enhanced content density  
        density_ratio = signals['text_density_ratio']
        density_score = min(density_ratio * 100.0 * 2, 100.0)  # Scale factor for better distribution
        subscores['content_density'] = density_score
        
        # Enhanced rich content scoring
        rich_content_score = 0.0
        code_count = signals['code_blocks_count']
        table_count = signals['tables_count']
        
        # More generous scoring for different content types
        if code_count >= 3:
            rich_content_score += 60.0
        elif code_count >= 1:
            rich_content_score += 30.0
            
        if table_count >= 2:
            rich_content_score += 40.0
        elif table_count >= 1:
            rich_content_score += 20.0
            
        # Bonus for diverse content
        if code_count > 0 and table_count > 0:
            rich_content_score += 10.0
            
        subscores['rich_content'] = min(rich_content_score, 100.0)
        
        # Enhanced boilerplate resistance
        boilerplate_ratio = signals['boilerplate_leakage_estimate']
        contamination_score = max(100.0 - (boilerplate_ratio * 100.0), 0.0)
        subscores['boilerplate_resistance'] = contamination_score
        
        return subscores
    
    def _simulate_agent_performance(self, parse_data: Dict) -> Dict[str, float]:
        """Simulate AI agent extraction performance."""
        
        try:
            # Load HTML content for analysis
            html_path = parse_data['html_path']
            if not Path(html_path).exists():
                return {'extraction_quality': 0, 'success_rate': 0}
                
            with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            return self._analyze_agent_extraction(html_content)
            
        except Exception as e:
            print(f"    [WARN] Agent simulation failed: {e}")
            return {'extraction_quality': 25, 'success_rate': 25}  # Fallback scores
    
    def _analyze_agent_extraction(self, html_content: str) -> Dict[str, float]:
        """Analyze HTML for agent extraction quality."""
        
        if not html_content or len(html_content) < 100:
            return {'extraction_quality': 0, 'success_rate': 0}
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove noise elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
            
        # Extract main content
        main_content = None
        content_selectors = ['main', 'article', '[role="main"]', '.content', '.main-content', '#content']
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element and len(element.get_text().strip()) > 200:
                main_content = element
                break
        
        if not main_content:
            main_content = soup.find('body') or soup
            for noise in main_content.find_all(['nav', 'header', 'footer', 'aside']):
                noise.decompose()
        
        # Assess extraction quality
        extracted_text = main_content.get_text() if main_content else ""
        clean_text = ' '.join(extracted_text.split())
        
        word_count = len(clean_text.split())
        sentence_count = len([s for s in re.split(r'[.!?]+', clean_text) if s.strip()])
        
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
            
        # Readability
        if word_count > 0 and sentence_count > 0:
            avg_words_per_sentence = word_count / sentence_count
            if 10 <= avg_words_per_sentence <= 25:
                quality_score += 10
                
        extraction_quality = min(100, quality_score)
        
        # Success rate (binary assessment)
        success_rate = 100 if (word_count >= 100 and sentence_count >= 2 and len(headings) >= 1) else 25
        
        return {
            'extraction_quality': extraction_quality,
            'success_rate': success_rate
        }
    
    def _classify_hybrid_failure_mode(self, overall_score: float, lighthouse_scores: Dict, 
                                    content_scores: Dict, agent_scores: Dict) -> str:
        """Enhanced failure mode classification for hybrid scoring."""
        
        # Agent-ready: High overall score with good agent performance
        if overall_score >= 75 and agent_scores['success_rate'] >= 75:
            return 'success'
        
        # Good with issues: Decent overall but some component problems
        if overall_score >= 50:
            if lighthouse_scores['accessibility'] < 60:
                return 'accessibility_issues'
            elif content_scores['content_density'] < 40:
                return 'content_sparse'  
            else:
                return 'good_with_issues'
        
        # Needs improvement: Low overall score
        if overall_score >= 25:
            return 'needs_improvement'
        
        # Critical issues: Very low score
        return 'critical_issues'
    
    def _gather_hybrid_evidence(self, signals: Dict, evidence: Dict, 
                              lighthouse_scores: Dict, agent_scores: Dict) -> List[str]:
        """Enhanced evidence gathering for hybrid methodology."""
        
        refs = []
        
        # Lighthouse evidence
        if lighthouse_scores['accessibility'] > 0:
            refs.append(f"Lighthouse accessibility: {lighthouse_scores['accessibility']:.1f}/100")
        if lighthouse_scores['seo'] > 0:
            refs.append(f"Lighthouse SEO: {lighthouse_scores['seo']:.1f}/100")
        if lighthouse_scores['performance'] > 0:
            refs.append(f"Lighthouse performance: {lighthouse_scores['performance']:.1f}/100")
        
        # Content analysis evidence (existing YARA logic)
        semantic_elements = evidence.get('semantic_elements', {})
        main_count = semantic_elements.get('main_count', 0)
        article_count = semantic_elements.get('article_count', 0)
        
        if main_count > 0:
            refs.append(f"Found {main_count} <main> element(s)")
        if article_count > 0:
            refs.append(f"Found {article_count} <article> element(s)")
            
        headings = evidence.get('heading_structure', [])
        if headings:
            refs.append(f"Heading structure: {len(headings)} headings")
        else:
            refs.append("No headings found")
        
        # Agent performance evidence
        refs.append(f"Agent extraction quality: {agent_scores['extraction_quality']:.1f}/100")
        refs.append(f"Agent success prediction: {agent_scores['success_rate']:.1f}/100")
        
        return refs