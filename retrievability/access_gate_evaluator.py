"""Clipper - Standards-Based Access Gate Evaluator.

Industry-standard, API-free evaluation for agent-ready content optimization.
Replaces API-dependent Lighthouse scoring with defensible standards-based methodology.
"""

import json
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin, urlparse
import logging

# Standards-based evaluation imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from axe_selenium_python import Axe
import extruct
from bs4 import BeautifulSoup, Comment
import html5lib
import httpx
import advertools
from pyquery import PyQuery as pq
import charset_normalizer

from .schemas import ScoreResult


class AccessGateEvaluator:
    """Clipper Standards-Based Access Gate Evaluator.
    
    Evaluates "Can agents reliably access Microsoft information?" using
    established industry frameworks with complete API independence.
    
    Standards Authority Mapping:
    - WCAG 2.1 AA (W3C) + axe-core (Deque Systems) - 25%
    - HTML5 Semantic Elements (W3C) - 25% 
    - Schema.org (Google/Microsoft/Yahoo) - 20%
    - RFC 7231 Content Negotiation (IETF) - 15%
    - Established content analysis metrics - 15%
    """
    
    # Evaluation weights (must sum to 1.0)
    WEIGHTS = {
        'wcag_accessibility': 0.25,     # WCAG 2.1 evaluation
        'semantic_html': 0.25,          # W3C semantic HTML analysis
        'structured_data': 0.20,        # Schema.org structured data
        'http_compliance': 0.15,        # HTTP standards compliance
        'content_quality': 0.15         # Agent-focused content metrics
    }
    
    # Standards authority documentation
    STANDARDS_AUTHORITY = {
        'accessibility': 'WCAG 2.1 AA (W3C) + axe-core (Deque Systems)',
        'semantics': 'HTML5 Semantic Elements (W3C)',
        'structured_data': 'Schema.org (Google/Microsoft/Yahoo)',
        'http_compliance': 'RFC 7231 Content Negotiation (IETF)',
        'content_quality': 'Established content analysis metrics'
    }
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        """Initialize the Access Gate Evaluator.
        
        Args:
            headless: Run browser in headless mode for WCAG evaluation
            timeout: HTTP timeout in seconds
        """
        self.headless = headless
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        # Chrome options for WCAG evaluation
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-web-security')
    
    def evaluate_access_gate(self, parse_data: Dict, url: Optional[str] = None, 
                             crawl_data: Optional[Dict] = None) -> ScoreResult:
        """Evaluate Access Gate score using industry standards.
        
        Args:
            parse_data: Dictionary containing parse result data
            url: URL for live standards evaluation (optional)
            crawl_data: Dictionary containing crawl result data with redirect chain (optional)
            
        Returns:
            ScoreResult with standards-based scores and audit trail
        """
        signals = parse_data['signals']
        evidence = parse_data['evidence']
        html_path = parse_data.get('html_path', '')
        
        # Load HTML content for analysis
        html_content = self._load_html_content(html_path)
        if not html_content:
            return self._create_error_result("Failed to load HTML content", html_path)
        
        # Component evaluations (all API-free, standards-based)
        scores = {}
        audit_trail = {}
        
        # 1. WCAG 2.1 Accessibility (25%) - Deque axe-core
        scores['wcag_accessibility'], audit_trail['wcag_accessibility'] = \
            self._evaluate_wcag_accessibility(html_content, url)
        
        # 2. W3C Semantic HTML (25%) - HTML5 semantic elements  
        scores['semantic_html'], audit_trail['semantic_html'] = \
            self._evaluate_semantic_html(html_content, signals)
        
        # 3. Schema.org Structured Data (20%) - extruct analysis
        scores['structured_data'], audit_trail['structured_data'] = \
            self._evaluate_structured_data(html_content, url)
        
        # 4. HTTP Standards Compliance (15%) - RFC 7231 + Redirect Efficiency
        scores['http_compliance'], audit_trail['http_compliance'] = \
            self._evaluate_http_compliance_enhanced(html_content, url, crawl_data)
        
        # 5. Content Quality (15%) - Agent-focused analysis
        scores['content_quality'], audit_trail['content_quality'] = \
            self._evaluate_content_quality(html_content, signals, evidence)
        
        # Calculate weighted final score
        final_score = sum(scores[component] * self.WEIGHTS[component] 
                         for component in scores)
        
        # Determine failure mode based on standards compliance
        failure_mode = self._determine_failure_mode_standards(scores, final_score)
        
        return ScoreResult(
            parseability_score=final_score,
            failure_mode=failure_mode,
            html_path=html_path,
            url=url or 'Unknown',
            component_scores=scores,
            audit_trail=audit_trail,
            standards_authority=self.STANDARDS_AUTHORITY,
            evaluation_methodology="Clipper Standards-Based Access Gate"
        )
    
    def _load_html_content(self, html_path: str) -> Optional[str]:
        """Load and normalize HTML content from file."""
        try:
            html_file = Path(html_path)
            
            # If path is not absolute, try to find it in common locations
            if not html_file.is_absolute():
                # Try relative to current directory
                if html_file.exists():
                    pass  # Use as-is
                else:
                    # Try in snapshots directory relative to current working directory
                    snapshots_path = Path.cwd() / "snapshots" / html_path
                    if snapshots_path.exists():
                        html_file = snapshots_path
                    else:
                        # Try looking in various common snapshot locations
                        possible_locations = [
                            Path.cwd() / "snapshots" / html_path,
                            Path.cwd() / "clipper-test-results" / "snapshots" / html_path,
                            Path(html_path).parent / "snapshots" / Path(html_path).name,
                            # Check all subdirectories with snapshots folders
                        ]
                        
                        # Also check for any directory ending with snapshots  
                        for item in Path.cwd().iterdir():
                            if item.is_dir():
                                snapshot_dir = item / "snapshots"
                                if snapshot_dir.exists():
                                    candidate = snapshot_dir / html_path
                                    if candidate.exists():
                                        possible_locations.append(candidate)
                        
                        for location in possible_locations:
                            if location.exists():
                                html_file = location
                                break
                        else:
                            self.logger.error(f"HTML file not found in any expected location: {html_path}")
                            self.logger.error(f"Searched in: {[str(loc) for loc in possible_locations]}")
                            return None
            
            if not html_file.exists():
                self.logger.error(f"HTML file not found: {html_file}")
                return None
            
            # Detect encoding and load content
            raw_content = html_file.read_bytes()
            detected_encoding = charset_normalizer.detect(raw_content)
            encoding = detected_encoding.get('encoding', 'utf-8')
            
            return raw_content.decode(encoding, errors='replace')
            
        except Exception as e:
            self.logger.error(f"Failed to load HTML content from {html_path}: {e}")
            return None
    
    def _evaluate_wcag_accessibility(self, html_content: str, url: Optional[str]) -> Tuple[float, Dict]:
        """Evaluate WCAG 2.1 accessibility using axe-core (Deque Systems standard).
        
        Returns:
            Tuple of (score 0-100, audit_trail_dict)
        """
        audit_trail = {
            'standard': 'WCAG 2.1 AA (W3C) + axe-core (Deque Systems)',
            'method': 'Automated accessibility evaluation',
            'violations': [],
            'passes': [],
            'score_calculation': 'Based on violation severity and frequency'
        }
        
        try:
            if url and self._is_valid_url(url):
                # Try live evaluation with Selenium + axe-core first
                try:
                    score, details = self._run_axe_evaluation(url)
                    audit_trail.update(details)
                    audit_trail['evaluation_method'] = 'Live browser with axe-core'
                    return score, audit_trail
                except Exception as axe_error:
                    self.logger.warning(f"[WARN] Axe browser evaluation failed, falling back to static analysis: {axe_error}")
                    # Fall back to static analysis when axe fails
                    audit_trail['axe_fallback_reason'] = str(axe_error)
                    audit_trail['evaluation_method'] = 'Static HTML analysis (axe-core unavailable)'
                    return self._evaluate_static_accessibility(html_content, audit_trail)
            else:
                # Static HTML analysis fallback
                audit_trail['evaluation_method'] = 'Static HTML analysis (no live URL)'
                return self._evaluate_static_accessibility(html_content, audit_trail)
                
        except Exception as e:
            self.logger.error(f"WCAG evaluation failed: {e}")
            audit_trail['error'] = str(e)
            return 0.0, audit_trail
    
    def _run_axe_evaluation(self, url: str) -> Tuple[float, Dict]:
        """Run axe-core accessibility evaluation on live URL."""
        driver = None
        try:
            # Setup Chrome driver with additional stability options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(self.timeout)
            driver.get(url)
            
            # Wait for page to load completely
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Run axe evaluation with proper injection
            axe = Axe(driver)
            
            # Critical fix: Inject axe-core JavaScript before running evaluation
            axe.inject()
            
            # Verify axe was injected successfully
            axe_available = driver.execute_script("return typeof axe !== 'undefined';")
            if not axe_available:
                raise Exception("axe-core injection failed - axe object not available in page")
            
            results = axe.run()
            
            # Calculate score based on violations
            violations = results.get('violations', [])
            passes = results.get('passes', [])
            
            # Scoring logic: 100 - (critical*25 + serious*15 + moderate*10 + minor*5)
            penalty = 0
            severity_weights = {'critical': 25, 'serious': 15, 'moderate': 10, 'minor': 5}
            
            for violation in violations:
                impact = violation.get('impact', 'minor')
                node_count = len(violation.get('nodes', []))
                penalty += severity_weights.get(impact, 5) * node_count
            
            score = max(0, 100 - penalty)
            
            return score, {
                'violations_count': len(violations),
                'passes_count': len(passes),
                'violations': violations[:10],  # Keep first 10 for audit trail
                'total_penalty': penalty
            }
            
        except Exception as e:
            self.logger.error(f"Axe evaluation failed for {url}: {e}")
            # Re-raise exception to trigger fallback to static analysis
            raise Exception(f"Browser accessibility evaluation failed: {e}")
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass  # Ignore cleanup errors
    
    def _evaluate_static_accessibility(self, html_content: str, audit_trail: Dict) -> Tuple[float, Dict]:
        """Fallback accessibility evaluation for static HTML."""
        soup = BeautifulSoup(html_content, 'html.parser')
        score = 70.0  # Base score for static analysis
        
        # Basic accessibility checks
        checks = {
            'has_lang_attribute': soup.find('html', attrs={'lang': True}) is not None,
            'has_title': soup.find('title') is not None and len(soup.find('title').get_text().strip()) > 0,
            'images_have_alt': self._check_image_alt_texts(soup),
            'headings_structured': self._check_heading_structure(soup),
            'links_descriptive': self._check_link_descriptions(soup)
        }
        
        # Adjust score based on checks
        passed_checks = sum(1 for passed in checks.values() if passed)
        score = (passed_checks / len(checks)) * 100
        
        audit_trail.update({
            'method': 'Static HTML accessibility analysis (fallback)',
            'checks_performed': checks,
            'passed_checks': f"{passed_checks}/{len(checks)}"
        })
        
        return score, audit_trail
    
    def _evaluate_semantic_html(self, html_content: str, signals: Dict) -> Tuple[float, Dict]:
        """Evaluate W3C HTML5 semantic elements usage.
        
        Returns:
            Tuple of (score 0-100, audit_trail_dict)
        """
        audit_trail = {
            'standard': 'HTML5 Semantic Elements (W3C)',
            'method': 'Semantic markup analysis',
            'elements_found': [],
            'score_calculation': 'Based on semantic element coverage and proper usage'
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html5lib')
            
            # HTML5 semantic elements to check
            semantic_elements = [
                'header', 'nav', 'main', 'article', 'section', 'aside', 
                'footer', 'figure', 'figcaption', 'time', 'mark'
            ]
            
            # ARIA landmarks and roles
            aria_elements = soup.find_all(attrs={'role': True})
            heading_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            
            # Score calculation
            found_semantic = []
            for element in semantic_elements:
                elements = soup.find_all(element)
                if elements:
                    found_semantic.append({
                        'element': element,
                        'count': len(elements),
                        'proper_usage': self._validate_semantic_usage(element, elements)
                    })
            
            # Calculate score
            base_score = (len(found_semantic) / len(semantic_elements)) * 60  # 60% for basic coverage
            aria_score = min(len(aria_elements) * 5, 20)  # Up to 20% for ARIA
            heading_score = min(len(heading_elements) * 2, 20)  # Up to 20% for headings
            
            final_score = min(base_score + aria_score + heading_score, 100)
            
            audit_trail.update({
                'semantic_elements_found': found_semantic,
                'aria_elements_count': len(aria_elements),
                'heading_elements_count': len(heading_elements),
                'scoring_breakdown': {
                    'semantic_coverage': base_score,
                    'aria_bonus': aria_score,
                    'heading_bonus': heading_score
                }
            })
            
            return final_score, audit_trail
            
        except Exception as e:
            self.logger.error(f"Semantic HTML evaluation failed: {e}")
            audit_trail['error'] = str(e)
            return 0.0, audit_trail
    
    def _evaluate_structured_data(self, html_content: str, url: Optional[str]) -> Tuple[float, Dict]:
        """Evaluate Schema.org structured data using extruct.
        
        Returns:
            Tuple of (score 0-100, audit_trail_dict)
        """
        audit_trail = {
            'standard': 'Schema.org (Google/Microsoft/Yahoo)',
            'method': 'Structured data extraction and validation',
            'formats_found': [],
            'score_calculation': 'Based on structured data richness and completeness'
        }
        
        try:
            # Extract structured data using extruct
            metadata = extruct.extract(
                html_content,
                base_url=url or '',
                syntaxes=['json-ld', 'microdata', 'opengraph', 'microformat']
            )
            
            # Score based on structured data richness
            score_components = {}
            
            # JSON-LD (preferred format) - up to 40 points
            json_ld_data = metadata.get('json-ld', [])
            score_components['json_ld'] = min(len(json_ld_data) * 10, 40)
            
            # Microdata - up to 25 points
            microdata = metadata.get('microdata', [])
            score_components['microdata'] = min(len(microdata) * 8, 25)
            
            # Open Graph - up to 20 points
            opengraph = metadata.get('opengraph', [])
            score_components['opengraph'] = min(len(opengraph) * 5, 20)
            
            # Microformats - up to 15 points
            microformat = metadata.get('microformat', [])
            score_components['microformat'] = min(len(microformat) * 3, 15)
            
            final_score = sum(score_components.values())
            
            audit_trail.update({
                'extracted_metadata': {
                    'json_ld_items': len(json_ld_data),
                    'microdata_items': len(microdata),
                    'opengraph_items': len(opengraph),
                    'microformat_items': len(microformat)
                },
                'score_breakdown': score_components,
                'sample_structured_data': self._sample_structured_data(metadata)
            })
            
            return final_score, audit_trail
            
        except Exception as e:
            self.logger.error(f"Structured data evaluation failed: {e}")
            audit_trail['error'] = str(e)
            return 0.0, audit_trail
    
    def _evaluate_http_compliance_enhanced(self, html_content: str, url: Optional[str], 
                                         crawl_data: Optional[Dict]) -> Tuple[float, Dict]:
        """Evaluate HTTP standards compliance with redirect efficiency analysis.
        
        Returns:
            Tuple of (score 0-100, audit_trail_dict)
        """
        audit_trail = {
            'standard': 'RFC 7231 Content Negotiation (IETF) + Redirect Efficiency',
            'method': 'Enhanced HTTP compliance with redirect chain analysis',
            'score_calculation': 'Content negotiation (60%) + Redirect efficiency (40%)'
        }
        
        try:
            # Get base HTTP compliance score (60% of component)
            base_score, base_audit = self._evaluate_http_compliance(html_content, url)
            content_nego_score = base_score * 0.6
            
            # New: Redirect efficiency scoring (40% of component)
            if crawl_data and 'redirect_chain' in crawl_data:
                redirect_score, redirect_audit = self._evaluate_redirect_efficiency(crawl_data)
            else:
                # Fallback: No redirect data available, assume optimal (no redirects)
                redirect_score = 40.0  # Full redirect efficiency score
                redirect_audit = {
                    'method': 'No redirect data available (assuming direct access)',
                    'redirect_efficiency_score': redirect_score,
                    'fallback_reason': 'Missing crawl data with redirect chain'
                }
            
            final_score = content_nego_score + redirect_score
            
            # Combine audit trails
            audit_trail.update({
                'content_negotiation': base_audit,
                'redirect_efficiency': redirect_audit,
                'scoring_breakdown': {
                    'content_negotiation_score': content_nego_score,
                    'redirect_efficiency_score': redirect_score,
                    'total_score': final_score
                }
            })
            
            return final_score, audit_trail
            
        except Exception as e:
            self.logger.error(f"Enhanced HTTP compliance evaluation failed: {e}")
            # Fallback to basic HTTP compliance
            return self._evaluate_http_compliance(html_content, url)
    
    def _evaluate_redirect_efficiency(self, crawl_data: Dict) -> Tuple[float, Dict]:
        """Evaluate redirect chain efficiency for HTTP compliance.
        
        Analyzes redirect chains for performance impact and standards compliance.
        
        Args:
            crawl_data: Dictionary containing redirect_chain and timing data
            
        Returns:
            Tuple of (score 0-40, audit_trail_dict)
        """
        audit_trail = {
            'standard': 'HTTP Redirect Best Practices (RFC 7231)',
            'method': 'Redirect chain analysis and performance evaluation',
            'score_calculation': 'Chain length (25) + Redirect types (10) + Performance (5)'
        }
        
        try:
            redirect_chain = crawl_data.get('redirect_chain', [])
            redirect_count = crawl_data.get('redirect_count', 0)
            total_redirect_time = crawl_data.get('total_redirect_time_ms', 0.0)
            final_response_time = crawl_data.get('final_response_time_ms', 1.0)
            
            score_components = {}
            
            # 1. Chain length scoring (0-25 points)
            if redirect_count == 0:
                score_components['chain_length'] = 25  # Perfect - no redirects
            elif redirect_count <= 2:
                score_components['chain_length'] = 20  # Good - reasonable redirects
            elif redirect_count <= 4:
                score_components['chain_length'] = 10  # Moderate - getting excessive
            else:
                score_components['chain_length'] = 0   # Poor - too many redirects
            
            # 2. Redirect type analysis (0-10 points)
            proper_redirects = 0
            redirect_types = {}
            
            for step in redirect_chain:
                status_code = step.get('status_code', 0)
                redirect_types[status_code] = redirect_types.get(status_code, 0) + 1
                if status_code in [301, 302, 303, 307, 308]:
                    proper_redirects += 1
            
            if redirect_count > 0:
                redirect_type_ratio = proper_redirects / redirect_count
                score_components['redirect_types'] = redirect_type_ratio * 10
            else:
                score_components['redirect_types'] = 10  # No redirects = perfect
            
            # 3. Performance impact analysis (0-5 points)
            if final_response_time > 0:
                redirect_ratio = total_redirect_time / (total_redirect_time + final_response_time)
                # Lower redirect ratio = better performance
                performance_score = max(5 - (redirect_ratio * 10), 0)
                score_components['performance_impact'] = min(performance_score, 5)
            else:
                score_components['performance_impact'] = 5
            
            final_score = sum(score_components.values())
            
            audit_trail.update({
                'redirect_analysis': {
                    'redirect_count': redirect_count,
                    'chain_details': redirect_chain[:3] if len(redirect_chain) <= 3 else redirect_chain[:3] + [{'truncated': f'{len(redirect_chain)-3} more redirects'}],
                    'redirect_types_breakdown': redirect_types,
                    'proper_redirect_codes': proper_redirects,
                    'total_redirect_time_ms': total_redirect_time,
                    'final_response_time_ms': final_response_time,
                    'performance_ratio': total_redirect_time / (total_redirect_time + final_response_time) if final_response_time > 0 else 0
                },
                'score_breakdown': score_components,
                'efficiency_classification': self._classify_redirect_efficiency(redirect_count, total_redirect_time)
            })
            
            return min(final_score, 40), audit_trail  # Cap at 40 points (40% of HTTP compliance)
            
        except Exception as e:
            self.logger.error(f"Redirect efficiency evaluation failed: {e}")
            audit_trail['error'] = str(e)
            return 40.0, audit_trail  # Default to full score on error
    
    def _classify_redirect_efficiency(self, redirect_count: int, total_redirect_time: float) -> str:
        """Classify redirect chain efficiency for reporting."""
        if redirect_count == 0:
            return 'optimal (direct access)'
        elif redirect_count <= 2 and total_redirect_time < 500:
            return 'good (standard redirects)'
        elif redirect_count <= 4 and total_redirect_time < 1000:
            return 'moderate (acceptable chain)'
        elif redirect_count <= 6:
            return 'poor (excessive redirects)'
        else:
            return 'critical (redirect chain too long)'

    def _evaluate_http_compliance(self, html_content: str, url: Optional[str]) -> Tuple[float, Dict]:
        """Evaluate HTTP standards compliance (RFC 7231).
        
        Returns:
            Tuple of (score 0-100, audit_trail_dict)
        """
        audit_trail = {
            'standard': 'RFC 7231 Content Negotiation (IETF)',
            'method': 'HTTP headers and content negotiation analysis',
            'score_calculation': 'Based on content negotiation support and header compliance'
        }
        
        try:
            score = 50.0  # Base score for static analysis
            
            if url and self._is_valid_url(url):
                # Test content negotiation with live URL
                score, details = self._test_content_negotiation(url)
                audit_trail.update(details)
            else:
                # Static HTML analysis for HTTP compliance indicators
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Check for content negotiation indicators
                meta_content_type = soup.find('meta', attrs={'http-equiv': 'Content-Type'})
                canonical_link = soup.find('link', rel='canonical')
                alternate_links = soup.find_all('link', rel='alternate')
                
                score_factors = {
                    'content_type_declared': bool(meta_content_type),
                    'canonical_url': bool(canonical_link),
                    'alternate_formats': len(alternate_links) > 0,
                    'proper_encoding_declaration': self._check_encoding_declaration(soup)
                }
                
                # Calculate score
                passed = sum(1 for passed in score_factors.values() if passed)
                score = (passed / len(score_factors)) * 100
                
                audit_trail.update({
                    'method': 'Static HTML compliance analysis (fallback)',
                    'compliance_factors': score_factors,
                    'alternate_formats_count': len(alternate_links)
                })
            
            return score, audit_trail
            
        except Exception as e:
            self.logger.error(f"HTTP compliance evaluation failed: {e}")
            audit_trail['error'] = str(e)
            return 0.0, audit_trail
    
    def _evaluate_content_quality(self, html_content: str, signals: Dict, evidence: Dict) -> Tuple[float, Dict]:
        """Evaluate agent-focused content quality metrics.
        
        Returns:
            Tuple of (score 0-100, audit_trail_dict)
        """
        audit_trail = {
            'standard': 'Established content analysis metrics',
            'method': 'Agent-focused content quality evaluation',
            'score_calculation': 'Based on content structure, readability, and agent accessibility'
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract text content
            text_content = soup.get_text()
            
            # Content quality metrics
            quality_metrics = {}
            
            # 1. Text-to-HTML ratio (from signals, fallback to calculation)
            text_html_ratio = signals.get('text_html_ratio', len(text_content) / len(html_content))
            quality_metrics['text_html_ratio'] = min(text_html_ratio * 100, 25)  # Up to 25 points
            
            # 2. Content structure (headings, paragraphs)
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            paragraphs = soup.find_all('p')
            quality_metrics['content_structure'] = min((len(headings) * 3 + len(paragraphs) * 0.5), 25)
            
            # 3. Link quality and navigation
            links = soup.find_all('a', href=True)
            internal_links = [link for link in links if not self._is_external_link(link.get('href', ''))]
            quality_metrics['navigation_quality'] = min(len(internal_links) * 2, 25)
            
            # 4. Content readability (basic metrics)
            words = len(text_content.split())
            sentences = text_content.count('.') + text_content.count('!') + text_content.count('?')
            avg_sentence_length = words / max(sentences, 1)
            readability_score = 100 - min(abs(avg_sentence_length - 15) * 2, 25)  # Optimal ~15 words/sentence
            quality_metrics['readability'] = min(max(readability_score, 0), 25)  # Cap at 25 points
            
            final_score = min(sum(quality_metrics.values()), 100)  # Cap total at 100
            
            audit_trail.update({
                'content_metrics': {
                    'total_text_length': len(text_content),
                    'total_html_length': len(html_content),
                    'text_html_ratio': text_html_ratio,
                    'headings_count': len(headings),
                    'paragraphs_count': len(paragraphs),
                    'links_count': len(links),
                    'internal_links_count': len(internal_links),
                    'avg_sentence_length': avg_sentence_length
                },
                'quality_breakdown': quality_metrics
            })
            
            return final_score, audit_trail
            
        except Exception as e:
            self.logger.error(f"Content quality evaluation failed: {e}")
            audit_trail['error'] = str(e)
            return 0.0, audit_trail
    
    def _determine_failure_mode_standards(self, scores: Dict[str, float], final_score: float) -> str:
        """Determine failure mode based on standards compliance."""
        if final_score >= 90:
            return 'clean'
        elif final_score >= 75:
            return 'minor_issues'
        elif final_score >= 60:
            return 'moderate_issues'
        elif final_score >= 40:
            return 'significant_issues'
        else:
            return 'severe_issues'
    
    def _create_error_result(self, error_message: str, html_path: str) -> ScoreResult:
        """Create error result for failed evaluations."""
        return ScoreResult(
            parseability_score=0.0,
            failure_mode='evaluation_error',
            html_path=html_path,
            url='Unknown',
            component_scores={},
            audit_trail={'error': error_message},
            standards_authority=self.STANDARDS_AUTHORITY,
            evaluation_methodology="Clipper Standards-Based Access Gate"
        )
    
    # Helper methods for specific evaluations
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid for live evaluation."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _check_image_alt_texts(self, soup: BeautifulSoup) -> bool:
        """Check if images have appropriate alt text."""
        images = soup.find_all('img')
        if not images:
            return True  # No images to check
        
        images_with_alt = [img for img in images if img.get('alt') is not None]
        return len(images_with_alt) / len(images) >= 0.8  # 80% threshold
    
    def _check_heading_structure(self, soup: BeautifulSoup) -> bool:
        """Check if heading structure is logical."""
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if not headings:
            return False
        
        # Check for h1 presence and reasonable structure
        h1_elements = soup.find_all('h1')
        return len(h1_elements) >= 1
    
    def _check_link_descriptions(self, soup: BeautifulSoup) -> bool:
        """Check if links have descriptive text."""
        links = soup.find_all('a', href=True)
        if not links:
            return True
        
        descriptive_links = []
        for link in links:
            text = link.get_text().strip()
            if text and len(text) > 3 and text.lower() not in ['click here', 'read more', 'more']:
                descriptive_links.append(link)
        
        return len(descriptive_links) / len(links) >= 0.7  # 70% threshold
    
    def _validate_semantic_usage(self, element_name: str, elements: List) -> bool:
        """Validate proper usage of semantic elements."""
        # Basic validation - could be expanded
        if element_name == 'main':
            return len(elements) == 1  # Should have exactly one main element
        elif element_name in ['header', 'footer']:
            return len(elements) <= 2  # Reasonable limit
        return True  # Default to valid
    
    def _sample_structured_data(self, metadata: Dict) -> Dict:
        """Create sample of structured data for audit trail."""
        sample = {}
        for format_name, data_list in metadata.items():
            if data_list and isinstance(data_list, list):
                sample[format_name] = data_list[:2]  # First 2 items only
        return sample
    
    def _test_content_negotiation(self, url: str) -> Tuple[float, Dict]:
        """Test HTTP content negotiation capabilities."""
        try:
            score = 0.0
            details = {}
            
            # Test different Accept headers
            accept_headers = [
                'text/html',
                'application/json',
                'text/markdown',
                'text/plain',
                'application/xml'
            ]
            
            responses = {}
            for accept in accept_headers:
                try:
                    response = httpx.get(
                        url,
                        headers={'Accept': accept},
                        timeout=self.timeout,
                        follow_redirects=True
                    )
                    responses[accept] = {
                        'status_code': response.status_code,
                        'content_type': response.headers.get('content-type', ''),
                        'content_length': len(response.content)
                    }
                except Exception as e:
                    responses[accept] = {'error': str(e)}
            
            # Score based on content negotiation support
            successful_negotiations = sum(1 for r in responses.values() 
                                        if 'status_code' in r and r['status_code'] == 200)
            score = (successful_negotiations / len(accept_headers)) * 100
            
            details.update({
                'content_negotiation_tests': responses,
                'successful_negotiations': successful_negotiations,
                'total_tests': len(accept_headers)
            })
            
            return score, details
            
        except Exception as e:
            return 0.0, {'error': str(e)}
    
    def _check_encoding_declaration(self, soup: BeautifulSoup) -> bool:
        """Check for proper character encoding declaration."""
        charset_meta = soup.find('meta', charset=True)
        content_type_meta = soup.find('meta', attrs={'http-equiv': 'Content-Type'})
        return bool(charset_meta or content_type_meta)
    
    def _is_external_link(self, href: str) -> bool:
        """Check if link is external."""
        if not href:
            return False
        return href.startswith('http://') or href.startswith('https://')