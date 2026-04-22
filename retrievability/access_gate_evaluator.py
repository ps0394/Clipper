"""Clipper - Standards-Based Access Gate Evaluator.

Industry-standard, API-free evaluation for agent-ready content optimization.
Uses established standards (W3C, Schema.org, WCAG, Mozilla Readability, RFC 7231).
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

# Mozilla Readability for content extractability evaluation
from readability import Document as ReadabilityDocument

from .schemas import ScoreResult
from . import __version__ as CLIPPER_VERSION
from .profiles import (
    PROFILE_ARTICLE,
    PROFILE_WEIGHTS,
    detect_content_type,
)


class PillarEvaluationError(Exception):
    """Raised when a pillar cannot be evaluated at all.

    The orchestrator catches this, records the pillar in ``failed_pillars``,
    and renormalizes the final score over the surviving pillars rather than
    treating the failure as a score of zero.
    """

    def __init__(self, pillar: str, reason: str):
        super().__init__(f"{pillar}: {reason}")
        self.pillar = pillar
        self.reason = reason


class AccessGateEvaluator:
    """Clipper Standards-Based Access Gate Evaluator.
    
    Evaluates "Can agents reliably access and use this content?" using
    established industry frameworks with complete API independence.
    
    Pillar Weights:
    - HTML5 Semantic Elements (W3C) - 25%
    - Content Extractability (Mozilla Readability) - 20%
    - Schema.org Structured Data - 20%
    - DOM Navigability (WCAG 2.1 / axe-core) - 15%
    - Metadata Completeness (Dublin Core / Schema.org / OpenGraph) - 10%
    - HTTP Compliance (RFC 7231 / robots / cache) - 10%
    """
    
    # Evaluation weights (must sum to 1.0)
    WEIGHTS = {
        'semantic_html': 0.25,              # W3C semantic HTML analysis
        'content_extractability': 0.20,     # Mozilla Readability content extraction
        'structured_data': 0.20,            # Schema.org structured data
        'dom_navigability': 0.15,           # WCAG 2.1 / axe-core DOM evaluation
        'metadata_completeness': 0.10,      # Dublin Core / Schema.org / OpenGraph metadata
        'http_compliance': 0.10             # Agent-focused HTTP compliance
    }
    
    # Standards authority documentation
    STANDARDS_AUTHORITY = {
        'semantic_html': 'HTML5 Semantic Elements (W3C)',
        'content_extractability': 'Mozilla Readability (Firefox Reader View algorithm)',
        'structured_data': 'Schema.org (Google/Microsoft/Yahoo)',
        'dom_navigability': 'WCAG 2.1 AA (W3C) + axe-core (Deque Systems)',
        'metadata_completeness': 'Dublin Core + Schema.org + OpenGraph',
        'http_compliance': 'RFC 7231 + robots.txt + Cache headers'
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
                             crawl_data: Optional[Dict] = None,
                             render_mode: str = 'rendered') -> ScoreResult:
        """Evaluate Access Gate score using industry standards.
        
        Args:
            parse_data: Dictionary containing parse result data
            url: URL for live standards evaluation (optional)
            crawl_data: Dictionary containing crawl result data with redirect chain (optional)
            render_mode: ``'rendered'`` (default) runs the full browser-axe
                pass for DOM navigability when a URL is available;
                ``'raw'`` forces the static-analysis fallback for DOM
                navigability and makes no browser call at all. Raw mode
                models agents that do not execute JavaScript.
            
        Returns:
            ScoreResult with standards-based scores and audit trail
        """
        if render_mode not in ('raw', 'rendered'):
            raise ValueError(f"render_mode must be 'raw' or 'rendered', got {render_mode!r}")

        signals = parse_data['signals']
        evidence = parse_data['evidence']
        html_path = parse_data.get('html_path', '')
        
        # Load HTML content for analysis
        html_content = self._load_html_content(html_path)
        if not html_content:
            return self._create_error_result("Failed to load HTML content", html_path)
        
        # Component evaluations (all API-free, standards-based).
        # In 'raw' mode DOM navigability is forced through its static
        # fallback so no browser/axe call occurs; this models a non-JS
        # agent's view of the page.
        if render_mode == 'raw':
            dom_nav_fn = lambda: self._evaluate_wcag_accessibility(html_content, None)
        else:
            dom_nav_fn = lambda: self._evaluate_wcag_accessibility(html_content, url)

        pillar_callables = [
            ('semantic_html',          lambda: self._evaluate_semantic_html(html_content, signals)),
            ('content_extractability', lambda: self._evaluate_content_extractability(html_content, signals)),
            ('structured_data',        lambda: self._evaluate_structured_data(html_content, url)),
            ('dom_navigability',       dom_nav_fn),
            ('metadata_completeness',  lambda: self._evaluate_metadata_completeness(html_content, url)),
            ('http_compliance',        lambda: self._evaluate_http_compliance_enhanced(html_content, url, crawl_data)),
        ]

        scores: Dict[str, float] = {}
        audit_trail: Dict[str, Any] = {}
        failed_pillars: List[str] = []

        for pillar_name, pillar_fn in pillar_callables:
            try:
                score_value, pillar_audit = pillar_fn()
                scores[pillar_name] = score_value
                audit_trail[pillar_name] = pillar_audit
            except PillarEvaluationError as e:
                failed_pillars.append(pillar_name)
                audit_trail[pillar_name] = {
                    'status': 'could_not_evaluate',
                    'reason': e.reason,
                }
                self.logger.error(f"Pillar '{pillar_name}' could not be evaluated: {e.reason}")

        # Record evaluator environment for reproducibility (Phase 0.3).
        audit_trail['_environment'] = self._capture_environment(audit_trail)

        partial_evaluation = bool(failed_pillars)

        # Detect content type and pick the weight profile (Phase 1.1). The
        # default ``article`` weights match the pre-1.1 behavior exactly, so
        # pages that fall through to the default keep producing the same
        # score as before.
        content_type, detection_trace = self._detect_content_type(html_content, url)
        profile_weights = PROFILE_WEIGHTS[content_type]
        audit_trail['_content_type'] = {
            'profile': content_type,
            'detection': detection_trace,
            'weights': profile_weights,
        }

        # Final score renormalizes over surviving pillar weights. If every
        # pillar failed the score is 0 and the failure mode reflects that.
        final_score = self._weighted_score(scores, profile_weights)
        universal_score = self._weighted_score(scores, PROFILE_WEIGHTS[PROFILE_ARTICLE])

        # Determine failure mode based on standards compliance
        failure_mode = self._determine_failure_mode_standards(
            scores, final_score, partial_evaluation=partial_evaluation
        )

        return ScoreResult(
            parseability_score=final_score,
            failure_mode=failure_mode,
            html_path=html_path,
            url=url or 'Unknown',
            component_scores=scores,
            audit_trail=audit_trail,
            standards_authority=self.STANDARDS_AUTHORITY,
            evaluation_methodology="Clipper Standards-Based Access Gate",
            partial_evaluation=partial_evaluation,
            failed_pillars=failed_pillars,
            content_type=content_type,
            universal_score=universal_score,
            render_mode=render_mode,
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
            raise PillarEvaluationError('dom_navigability', str(e)) from e

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
            
            # Scoring logic: 100 - sum of capped per-rule penalties
            # Diminishing returns: only first 3 nodes per rule count fully
            # Cap: no single rule can cost more than 25 points
            MAX_PENALTY_PER_RULE = 25
            penalty = 0
            severity_weights = {'critical': 25, 'serious': 15, 'moderate': 10, 'minor': 5}
            penalty_per_rule = {}
            
            for violation in violations:
                impact = violation.get('impact', 'minor')
                node_count = len(violation.get('nodes', []))
                rule_id = violation.get('id', 'unknown')
                rule_penalty = severity_weights.get(impact, 5) * min(node_count, 3)
                capped_penalty = min(rule_penalty, MAX_PENALTY_PER_RULE)
                penalty_per_rule[rule_id] = {
                    'impact': impact,
                    'node_count': node_count,
                    'raw_penalty': severity_weights.get(impact, 5) * node_count,
                    'capped_penalty': capped_penalty
                }
                penalty += capped_penalty
            
            score = max(0, 100 - penalty)

            # Capture tool versions so Phase 0.3 reproducibility metadata
            # has something to report for the live-browser path.
            browser_version = driver.capabilities.get('browserVersion') \
                or driver.capabilities.get('version', 'unknown')
            chromedriver_version = (
                driver.capabilities.get('chrome', {}).get('chromedriverVersion', 'unknown')
            )
            axe_version = results.get('testEngine', {}).get('version', 'unknown')

            return score, {
                'violations_count': len(violations),
                'passes_count': len(passes),
                'violations': violations[:10],  # Keep first 10 for audit trail
                'total_penalty': penalty,
                'penalty_per_rule': penalty_per_rule,
                'browser_version': browser_version,
                'chromedriver_version': chromedriver_version,
                'axe_version': axe_version,
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
            raise PillarEvaluationError('semantic_html', str(e)) from e
    
    def _evaluate_structured_data(self, html_content: str, url: Optional[str]) -> Tuple[float, Dict]:
        """Evaluate Schema.org structured data quality and completeness.
        
        Returns:
            Tuple of (score 0-100, audit_trail_dict)
        """
        audit_trail = {
            'standard': 'Schema.org (Google/Microsoft/Yahoo)',
            'method': 'Structured data quality and completeness validation',
            'formats_found': [],
            'score_calculation': 'Type appropriateness (20) + Field completeness (30) + Multiple formats (20) + Schema validation (30)'
        }
        
        try:
            # Extract structured data using extruct
            metadata = extruct.extract(
                html_content,
                base_url=url or '',
                syntaxes=['json-ld', 'microdata', 'opengraph', 'microformat']
            )
            
            json_ld_data = metadata.get('json-ld', [])
            microdata = metadata.get('microdata', [])
            opengraph = metadata.get('opengraph', [])
            microformat = metadata.get('microformat', [])
            
            score_components = {}
            
            # 1. Schema type appropriateness (0-20 points)
            # Does the @type match common content types?
            type_score = 0
            schema_types = []
            content_types = {
                'Article', 'TechArticle', 'HowTo', 'WebPage', 'WebSite',
                'FAQPage', 'APIReference', 'SoftwareApplication',
                'Organization', 'Person', 'Product', 'BreadcrumbList',
                'ItemList', 'CollectionPage', 'AboutPage', 'ContactPage',
                'CreativeWork', 'DigitalDocument', 'Report', 'ScholarlyArticle',
                'BlogPosting', 'NewsArticle', 'Course', 'Event', 'Review'
            }
            for item in json_ld_data:
                if isinstance(item, dict):
                    schema_type = item.get('@type', '')
                    if isinstance(schema_type, list):
                        schema_types.extend(schema_type)
                    else:
                        schema_types.append(schema_type)
            
            if schema_types:
                matched = sum(1 for t in schema_types if t in content_types)
                type_score = min((matched / max(len(schema_types), 1)) * 20, 20)
            score_components['type_appropriateness'] = type_score
            
            # 2. Field completeness (0-30 points)
            # Does JSON-LD include key fields?
            key_fields = ['name', 'description', 'dateModified', 'author', 'publisher',
                         'headline', 'datePublished', 'image', 'url']
            fields_found = set()
            for item in json_ld_data:
                if isinstance(item, dict):
                    for field in key_fields:
                        if item.get(field):
                            fields_found.add(field)
            
            if key_fields:
                completeness_ratio = len(fields_found) / len(key_fields)
                score_components['field_completeness'] = completeness_ratio * 30
            else:
                score_components['field_completeness'] = 0
            
            # 3. Multiple formats (0-20 points)
            # JSON-LD + OpenGraph + microdata present?
            formats_present = sum([
                bool(json_ld_data),
                bool(opengraph),
                bool(microdata),
                bool(microformat)
            ])
            # 1 format = 5, 2 = 12, 3 = 17, 4 = 20
            format_scores = {0: 0, 1: 5, 2: 12, 3: 17, 4: 20}
            score_components['multiple_formats'] = format_scores.get(formats_present, 20)
            
            # 4. Schema.org validation (0-30 points)
            # Are required properties present for the declared type?
            validation_score = 0
            # Common required fields by type
            type_required_fields = {
                'Article': ['headline', 'author', 'datePublished'],
                'TechArticle': ['headline', 'author', 'datePublished'],
                'WebPage': ['name', 'description'],
                'WebSite': ['name', 'url'],
                'Organization': ['name', 'url'],
                'BreadcrumbList': ['itemListElement'],
                'FAQPage': ['mainEntity'],
                'HowTo': ['name', 'step'],
                'Product': ['name', 'description'],
            }
            
            validated_types = 0
            total_types_checked = 0
            for item in json_ld_data:
                if isinstance(item, dict):
                    schema_type = item.get('@type', '')
                    if isinstance(schema_type, list):
                        schema_type = schema_type[0] if schema_type else ''
                    required = type_required_fields.get(schema_type)
                    if required:
                        total_types_checked += 1
                        present = sum(1 for f in required if item.get(f))
                        if present == len(required):
                            validated_types += 1
                        else:
                            validated_types += present / len(required) * 0.5
            
            if total_types_checked > 0:
                validation_score = (validated_types / total_types_checked) * 30
            elif json_ld_data:
                # Has JSON-LD but unrecognized types — give partial credit
                validation_score = 10
            score_components['schema_validation'] = validation_score
            
            final_score = min(sum(score_components.values()), 100)
            
            audit_trail.update({
                'extracted_metadata': {
                    'json_ld_items': len(json_ld_data),
                    'microdata_items': len(microdata),
                    'opengraph_items': len(opengraph),
                    'microformat_items': len(microformat)
                },
                'schema_types_found': schema_types,
                'key_fields_found': list(fields_found),
                'formats_present': formats_present,
                'score_breakdown': score_components,
                'sample_structured_data': self._sample_structured_data(metadata)
            })
            
            return final_score, audit_trail
            
        except Exception as e:
            self.logger.error(f"Structured data evaluation failed: {e}")
            audit_trail['error'] = str(e)
            raise PillarEvaluationError('structured_data', str(e)) from e
    
    def _evaluate_http_compliance_enhanced(self, html_content: str, url: Optional[str], 
                                         crawl_data: Optional[Dict]) -> Tuple[float, Dict]:
        """Evaluate HTTP standards compliance: accessibility for agents.
        
        Focused on what matters for agent retrieval:
        - HTML reachability (text/html response)
        - Redirect efficiency
        - robots.txt / meta robots (crawl permissions)
        - Cache headers (ETag, Last-Modified, Cache-Control)
        
        Returns:
            Tuple of (score 0-100, audit_trail_dict)
        """
        audit_trail = {
            'standard': 'RFC 7231 + robots.txt + Cache headers',
            'method': 'Agent-focused HTTP compliance evaluation',
            'score_calculation': 'HTML reachability (15) + Redirect efficiency (25) + Robots/crawl permissions (20) + Cache headers (20) + Agent content hints (20)'
        }
        
        try:
            score_components = {}
            
            # 1. HTML reachability (0-15 points) — does the URL serve text/html?
            html_reach_score = 0
            html_reach_audit = {}
            if url and self._is_valid_url(url):
                try:
                    response = httpx.get(
                        url,
                        headers={'Accept': 'text/html'},
                        timeout=self.timeout,
                        follow_redirects=True
                    )
                    html_reach_audit['status_code'] = response.status_code
                    html_reach_audit['content_type'] = response.headers.get('content-type', '')
                    if response.status_code == 200:
                        html_reach_score = 15
                    elif response.status_code in (301, 302, 307, 308):
                        html_reach_score = 11
                    elif response.status_code < 400:
                        html_reach_score = 8
                    else:
                        html_reach_score = 0
                except Exception as e:
                    html_reach_audit['error'] = str(e)
                    html_reach_score = 0
            else:
                html_reach_score = 11
                html_reach_audit['method'] = 'Static fallback (no live URL)'
            score_components['html_reachability'] = html_reach_score
            audit_trail['html_reachability'] = html_reach_audit
            
            # 2. Redirect efficiency (0-25 points)
            if crawl_data and 'redirect_chain' in crawl_data:
                redirect_score, redirect_audit = self._evaluate_redirect_efficiency(crawl_data)
                score_components['redirect_efficiency'] = (redirect_score / 40) * 25
            else:
                score_components['redirect_efficiency'] = 25.0
                redirect_audit = {'method': 'No redirect data (assuming direct access)'}
            audit_trail['redirect_efficiency'] = redirect_audit
            
            # 3. Robots / crawl permissions (0-20 points)
            robots_score = 0
            robots_audit = {}
            
            # Check <meta name="robots"> in HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            meta_robots = soup.find('meta', attrs={'name': lambda n: n and n.lower() == 'robots'})
            if meta_robots:
                robots_content = (meta_robots.get('content', '') or '').lower()
                robots_audit['meta_robots'] = robots_content
                has_noindex = 'noindex' in robots_content
                has_nofollow = 'nofollow' in robots_content
                if has_noindex:
                    robots_score = 0
                    robots_audit['blocked'] = True
                elif has_nofollow:
                    robots_score = 10
                else:
                    robots_score = 12
            else:
                robots_score = 12
                robots_audit['meta_robots'] = 'none (permissive by default)'
            
            # Check robots.txt (if live URL available)
            if url and self._is_valid_url(url):
                try:
                    parsed = urlparse(url)
                    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
                    robots_response = httpx.get(robots_url, timeout=10, follow_redirects=True)
                    robots_audit['robots_txt_status'] = robots_response.status_code
                    if robots_response.status_code == 200:
                        robots_text = robots_response.text
                        path = parsed.path or '/'
                        is_blocked = self._check_robots_txt_blocked(robots_text, path)
                        if is_blocked:
                            robots_score = max(robots_score - 12, 0)
                            robots_audit['robots_txt_blocked'] = True
                        else:
                            robots_score += 8
                            robots_audit['robots_txt_blocked'] = False
                    else:
                        robots_score += 8  # No robots.txt = permissive
                        robots_audit['robots_txt_blocked'] = False
                except Exception as e:
                    robots_score += 4  # Can't check, partial credit
                    robots_audit['robots_txt_error'] = str(e)
            else:
                robots_score += 4  # No URL to check
            
            score_components['crawl_permissions'] = min(robots_score, 20)
            audit_trail['crawl_permissions'] = robots_audit
            
            # 4. Cache headers (0-20 points)
            cache_score = 0
            cache_audit = {}
            if url and self._is_valid_url(url):
                try:
                    head_response = httpx.head(url, timeout=10, follow_redirects=True)
                    headers = head_response.headers
                    
                    has_etag = 'etag' in headers
                    has_last_modified = 'last-modified' in headers
                    has_cache_control = 'cache-control' in headers
                    
                    cache_audit['etag'] = headers.get('etag', 'absent')
                    cache_audit['last_modified'] = headers.get('last-modified', 'absent')
                    cache_audit['cache_control'] = headers.get('cache-control', 'absent')
                    
                    if has_etag:
                        cache_score += 8
                    if has_last_modified:
                        cache_score += 8
                    if has_cache_control:
                        cc = headers.get('cache-control', '').lower()
                        if 'no-store' in cc:
                            cache_score += 1
                        else:
                            cache_score += 4
                except Exception as e:
                    cache_audit['error'] = str(e)
            else:
                cache_score = 10
                cache_audit['method'] = 'Static fallback (no live URL)'
            
            score_components['cache_headers'] = min(cache_score, 20)
            audit_trail['cache_headers'] = cache_audit
            
            # 5. Agent content hints (0-20 points) — does the HTML declare
            #    machine-readable alternate formats or LLM-specific endpoints?
            agent_hints_score = 0
            agent_hints_audit = {}
            
            # Re-use the soup already created for robots check
            from .parse import _detect_agent_content_hints
            hints = _detect_agent_content_hints(soup)
            agent_hints_audit['signals_found'] = hints
            
            if hints.get('has_markdown_alternate'):
                agent_hints_score += 6   # <link rel="alternate" type="text/markdown">
            if hints.get('has_markdown_url_meta'):
                agent_hints_score += 4   # <meta name="markdown_url">
            if hints.get('has_llm_hints'):
                agent_hints_score += 4   # data-llm-hint attributes
            if hints.get('has_llms_txt_ref'):
                agent_hints_score += 3   # llms.txt reference
            if hints.get('has_non_html_alternate'):
                agent_hints_score += 3   # any non-HTML <link rel="alternate">
            
            score_components['agent_content_hints'] = min(agent_hints_score, 20)
            audit_trail['agent_content_hints'] = agent_hints_audit
            
            final_score = min(sum(score_components.values()), 100)
            audit_trail['score_breakdown'] = score_components
            
            return final_score, audit_trail
            
        except Exception as e:
            self.logger.error(f"HTTP compliance evaluation failed: {e}")
            audit_trail['error'] = str(e)
            raise PillarEvaluationError('http_compliance', str(e)) from e
    
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

    def _evaluate_content_extractability(self, html_content: str, signals: Dict) -> Tuple[float, Dict]:
        """Evaluate content extractability using Mozilla Readability algorithm.
        
        Measures how cleanly an agent can extract meaningful content from the page,
        using the same algorithm as Firefox Reader View.
        
        Returns:
            Tuple of (score 0-100, audit_trail_dict)
        """
        audit_trail = {
            'standard': 'Mozilla Readability (Firefox Reader View algorithm)',
            'method': 'Content extraction completeness and cleanliness analysis',
            'score_calculation': 'Signal-to-noise (40) + Structure preservation (30) + Boundary detection (30)'
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            raw_text = soup.get_text(separator=' ', strip=True)
            raw_text_length = len(raw_text)
            
            if raw_text_length == 0:
                audit_trail['error'] = 'No text content found in page'
                return 0.0, audit_trail
            
            # Run Mozilla Readability extraction
            doc = ReadabilityDocument(html_content)
            extracted_html = doc.summary()
            extracted_title = doc.short_title()
            
            extracted_soup = BeautifulSoup(extracted_html, 'html.parser')
            extracted_text = extracted_soup.get_text(separator=' ', strip=True)
            extracted_text_length = len(extracted_text)
            
            score_components = {}
            
            # 1. Signal-to-noise ratio (0-40 points)
            # Ratio of extracted meaningful text to raw page text
            if raw_text_length > 0:
                extraction_ratio = extracted_text_length / raw_text_length
                # Optimal: 0.3-0.8 (page has content with some chrome removed)
                # Too low (<0.1): readability couldn't find content
                # Too high (>0.9): page is mostly content (good) or extraction failed to filter
                if extraction_ratio < 0.05:
                    ratio_score = extraction_ratio * 200  # Very low extraction = poor
                elif extraction_ratio < 0.15:
                    ratio_score = 10 + (extraction_ratio - 0.05) * 200
                elif extraction_ratio <= 0.85:
                    ratio_score = 30 + (min(extraction_ratio, 0.7) / 0.7) * 10  # Good range
                else:
                    ratio_score = 35  # Very high ratio is still good
                score_components['signal_to_noise'] = min(ratio_score, 40)
            else:
                score_components['signal_to_noise'] = 0
            
            # 2. Structure preservation (0-30 points)
            # Do headings, lists, and code blocks survive extraction?
            original_headings = len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
            extracted_headings = len(extracted_soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
            
            original_lists = len(soup.find_all(['ul', 'ol']))
            extracted_lists = len(extracted_soup.find_all(['ul', 'ol']))
            
            original_code = len(soup.find_all(['pre', 'code']))
            extracted_code = len(extracted_soup.find_all(['pre', 'code']))
            
            structure_score = 0
            # Headings preservation (0-10)
            if original_headings > 0:
                heading_ratio = min(extracted_headings / original_headings, 1.0)
                structure_score += heading_ratio * 10
            else:
                structure_score += 5  # No headings to preserve — neutral
            
            # Lists preservation (0-10)
            if original_lists > 0:
                list_ratio = min(extracted_lists / original_lists, 1.0)
                structure_score += list_ratio * 10
            else:
                structure_score += 5  # Neutral
            
            # Code blocks preservation (0-10)
            if original_code > 0:
                code_ratio = min(extracted_code / original_code, 1.0)
                structure_score += code_ratio * 10
            else:
                structure_score += 5  # Neutral
            
            score_components['structure_preservation'] = min(structure_score, 30)
            
            # 3. Content boundary detection (0-30 points)
            # Did readability find a clear article boundary?
            boundary_score = 0
            
            # Check if a title was extracted
            if extracted_title and len(extracted_title.strip()) > 0:
                boundary_score += 10
            
            # Check if extraction produced meaningful content (>100 chars)
            if extracted_text_length > 100:
                boundary_score += 10
            elif extracted_text_length > 20:
                boundary_score += 5
            
            # Check if main content region exists in original (helps readability)
            main_element = soup.find('main') or soup.find('article')
            if main_element:
                main_text = main_element.get_text(separator=' ', strip=True)
                main_text_length = len(main_text)
                # How much of <main> content survived extraction?
                if main_text_length > 0 and extracted_text_length > 0:
                    # Use word overlap as a rough measure
                    main_words = set(main_text.lower().split()[:200])
                    extracted_words = set(extracted_text.lower().split()[:200])
                    if main_words:
                        overlap = len(main_words & extracted_words) / len(main_words)
                        boundary_score += overlap * 10
                    else:
                        boundary_score += 5
                else:
                    boundary_score += 5
            else:
                # No <main>/<article> — readability has to guess boundaries
                boundary_score += 3
            
            score_components['boundary_detection'] = min(boundary_score, 30)
            
            final_score = min(sum(score_components.values()), 100)
            
            audit_trail.update({
                'extraction_metrics': {
                    'raw_text_length': raw_text_length,
                    'extracted_text_length': extracted_text_length,
                    'extracted_chars': extracted_text_length,
                    'extraction_ratio': round(extracted_text_length / raw_text_length, 3) if raw_text_length > 0 else 0,
                    'extracted_title': extracted_title,
                    'extracted_preview': (extracted_text[:300] + '...') if extracted_text_length > 300 else extracted_text,
                    'original_headings': original_headings,
                    'extracted_headings': extracted_headings,
                    'original_lists': original_lists,
                    'extracted_lists': extracted_lists,
                    'original_code_blocks': original_code,
                    'extracted_code_blocks': extracted_code,
                    'has_main_element': bool(soup.find('main')),
                    'has_article_element': bool(soup.find('article'))
                },
                'score_breakdown': score_components
            })
            
            return final_score, audit_trail
            
        except Exception as e:
            self.logger.error(f"Content extractability evaluation failed: {e}")
            audit_trail['error'] = str(e)
            raise PillarEvaluationError('content_extractability', str(e)) from e
    
    def _evaluate_metadata_completeness(self, html_content: str, url: Optional[str]) -> Tuple[float, Dict]:
        """Evaluate metadata completeness across Dublin Core, Schema.org, and OpenGraph.
        
        Checks for the presence of key metadata fields that agents use
        to understand page identity, authorship, and currency.
        
        Returns:
            Tuple of (score 0-100, audit_trail_dict)
        """
        audit_trail = {
            'standard': 'Dublin Core + Schema.org + OpenGraph metadata',
            'method': 'Metadata field presence and quality check',
            'score_calculation': 'Sum of field scores (title 15, description 15, author 15, date 15, topic 15, language 10, canonical 15)'
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract JSON-LD for Schema.org fields
            json_ld_data = {}
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(script.string or '{}')
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                json_ld_data.update(item)
                    elif isinstance(data, dict):
                        json_ld_data.update(data)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            field_scores = {}
            field_sources = {}
            
            # 1. Title (15 points) — <title>, og:title, or Schema.org name
            title_tag = soup.find('title')
            og_title = soup.find('meta', property='og:title')
            schema_name = json_ld_data.get('name') or json_ld_data.get('headline')
            has_title = bool(
                (title_tag and title_tag.get_text(strip=True)) or
                (og_title and og_title.get('content', '').strip()) or
                schema_name
            )
            field_scores['title'] = 15 if has_title else 0
            field_sources['title'] = [
                s for s, v in [
                    ('title_tag', title_tag and title_tag.get_text(strip=True)),
                    ('og:title', og_title and og_title.get('content', '').strip()),
                    ('schema:name', schema_name)
                ] if v
            ]
            
            # 2. Description (15 points) — <meta name="description">, og:description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            og_desc = soup.find('meta', property='og:description')
            schema_desc = json_ld_data.get('description')
            has_desc = bool(
                (meta_desc and meta_desc.get('content', '').strip()) or
                (og_desc and og_desc.get('content', '').strip()) or
                schema_desc
            )
            field_scores['description'] = 15 if has_desc else 0
            field_sources['description'] = [
                s for s, v in [
                    ('meta:description', meta_desc and meta_desc.get('content', '').strip()),
                    ('og:description', og_desc and og_desc.get('content', '').strip()),
                    ('schema:description', schema_desc)
                ] if v
            ]
            
            # 3. Author/Publisher (15 points)
            meta_author = soup.find('meta', attrs={'name': 'author'})
            schema_author = json_ld_data.get('author')
            schema_publisher = json_ld_data.get('publisher')
            has_author = bool(
                (meta_author and meta_author.get('content', '').strip()) or
                schema_author or schema_publisher
            )
            field_scores['author'] = 15 if has_author else 0
            field_sources['author'] = [
                s for s, v in [
                    ('meta:author', meta_author and meta_author.get('content', '').strip()),
                    ('schema:author', schema_author),
                    ('schema:publisher', schema_publisher)
                ] if v
            ]
            
            # 4. Date published/modified (15 points)
            meta_date = soup.find('meta', attrs={'name': lambda n: n and 'date' in n.lower()}) if soup.find('meta', attrs={'name': True}) else None
            time_element = soup.find('time', attrs={'datetime': True})
            schema_date = json_ld_data.get('dateModified') or json_ld_data.get('datePublished')
            has_date = bool(
                (meta_date and meta_date.get('content', '').strip()) or
                time_element or schema_date
            )
            field_scores['date'] = 15 if has_date else 0
            field_sources['date'] = [
                s for s, v in [
                    ('meta:date', meta_date and meta_date.get('content', '').strip()),
                    ('time_element', time_element and time_element.get('datetime', '')),
                    ('schema:date', schema_date)
                ] if v
            ]
            
            # 5. Topic/Category (15 points)
            meta_topic = soup.find('meta', attrs={'name': lambda n: n and n.lower() in ('ms.topic', 'topic', 'category', 'keywords')}) if soup.find('meta', attrs={'name': True}) else None
            schema_section = json_ld_data.get('articleSection')
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            has_topic = bool(
                (meta_topic and meta_topic.get('content', '').strip()) or
                schema_section or
                (meta_keywords and meta_keywords.get('content', '').strip())
            )
            field_scores['topic'] = 15 if has_topic else 0
            field_sources['topic'] = [
                s for s, v in [
                    ('meta:topic', meta_topic and meta_topic.get('content', '').strip()),
                    ('schema:articleSection', schema_section),
                    ('meta:keywords', meta_keywords and meta_keywords.get('content', '').strip())
                ] if v
            ]
            
            # 6. Language (10 points)
            html_lang = soup.find('html', attrs={'lang': True})
            meta_lang = soup.find('meta', attrs={'http-equiv': lambda v: v and v.lower() == 'content-language'})
            has_lang = bool(
                (html_lang and html_lang.get('lang', '').strip()) or
                (meta_lang and meta_lang.get('content', '').strip())
            )
            field_scores['language'] = 10 if has_lang else 0
            field_sources['language'] = [
                s for s, v in [
                    ('html:lang', html_lang and html_lang.get('lang', '').strip()),
                    ('meta:content-language', meta_lang and meta_lang.get('content', '').strip())
                ] if v
            ]
            
            # 7. Canonical URL (15 points)
            canonical = soup.find('link', rel='canonical')
            has_canonical = bool(canonical and canonical.get('href', '').strip())
            field_scores['canonical_url'] = 15 if has_canonical else 0
            field_sources['canonical_url'] = [
                s for s, v in [
                    ('link:canonical', canonical and canonical.get('href', '').strip())
                ] if v
            ]
            
            final_score = sum(field_scores.values())
            
            audit_trail.update({
                'field_scores': field_scores,
                'field_sources': field_sources,
                'fields_present': sum(1 for v in field_scores.values() if v > 0),
                'fields_total': len(field_scores),
                'json_ld_type': json_ld_data.get('@type', 'none')
            })
            
            return min(final_score, 100), audit_trail
            
        except Exception as e:
            self.logger.error(f"Metadata completeness evaluation failed: {e}")
            audit_trail['error'] = str(e)
            raise PillarEvaluationError('metadata_completeness', str(e)) from e
    
    def _determine_failure_mode_standards(
        self,
        scores: Dict[str, float],
        final_score: float,
        partial_evaluation: bool = False,
    ) -> str:
        """Determine failure mode based on standards compliance.

        When a run could not evaluate every pillar, the final score is a
        weighted average over the survivors — possibly inflated or deflated
        relative to a full run. Flag those cases so downstream tooling can
        treat the score with appropriate caution.
        """
        if not scores:
            return 'evaluation_error'
        if partial_evaluation:
            return 'partial_evaluation'
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

    def _weighted_score(
        self,
        scores: Dict[str, float],
        weights: Dict[str, float],
    ) -> float:
        """Weighted average over only the pillars present in ``scores``.

        When some pillars failed evaluation, this renormalizes the remaining
        weights so the final number still sits on the 0-100 scale.
        """
        if not scores:
            return 0.0
        surviving_weight = sum(weights[p] for p in scores if p in weights)
        if surviving_weight <= 0:
            return 0.0
        return sum(
            scores[p] * weights[p] for p in scores if p in weights
        ) / surviving_weight

    def _detect_content_type(
        self,
        html_content: str,
        url: Optional[str],
    ) -> Tuple[str, Dict[str, str]]:
        """Thin wrapper around :func:`detect_content_type` for DI / testing."""
        soup = BeautifulSoup(html_content, 'html.parser')
        return detect_content_type(soup, url)

    def _capture_environment(self, audit_trail: Dict[str, Any]) -> Dict[str, Any]:
        """Capture evaluator environment metadata for reproducibility.

        Records Clipper version, Python version, platform, and known
        library versions. Browser and axe-core versions are populated only
        when the WCAG pillar successfully ran against a live URL (that path
        writes them into its own audit block); the helper copies them up
        here so consumers have a single place to look.
        """
        import platform
        import sys

        env: Dict[str, Any] = {
            'clipper_version': CLIPPER_VERSION,
            'python_version': sys.version.split()[0],
            'platform': platform.platform(),
        }

        # Library versions we care about for scoring reproducibility.
        for pkg in ('beautifulsoup4', 'readability-lxml', 'extruct',
                    'httpx', 'axe-selenium-python', 'selenium'):
            try:
                import importlib.metadata as importlib_metadata
                env[pkg] = importlib_metadata.version(pkg)
            except Exception:
                env[pkg] = 'unknown'

        # Surface browser/axe versions if WCAG pillar captured them.
        wcag_audit = audit_trail.get('dom_navigability', {}) or {}
        for key in ('browser_version', 'chromedriver_version', 'axe_version'):
            if key in wcag_audit:
                env[key] = wcag_audit[key]

        return env
    
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
    
    def _check_robots_txt_blocked(self, robots_text: str, path: str) -> bool:
        """Parse robots.txt and check if the path is blocked for generic agents.
        
        Respects User-agent directives: only considers rules under User-agent: *
        (the wildcard block that applies to unnamed/generic crawlers).
        
        Args:
            robots_text: Raw robots.txt content
            path: URL path to check (e.g. '/docs/overview')
            
        Returns:
            True if the path is disallowed for generic agents
        """
        in_wildcard_block = False
        wildcard_rules = []  # List of (allow: bool, path_pattern: str)
        
        for line in robots_text.splitlines():
            line = line.split('#', 1)[0].strip()  # Strip comments
            if not line:
                continue
            
            lower_line = line.lower()
            
            if lower_line.startswith('user-agent:'):
                agent = line.split(':', 1)[1].strip()
                in_wildcard_block = agent == '*'
            elif in_wildcard_block:
                if lower_line.startswith('disallow:'):
                    rule_path = line.split(':', 1)[1].strip()
                    if rule_path:  # Empty Disallow means allow all
                        wildcard_rules.append((False, rule_path))
                elif lower_line.startswith('allow:'):
                    rule_path = line.split(':', 1)[1].strip()
                    if rule_path:
                        wildcard_rules.append((True, rule_path))
        
        # Match rules: longest matching path wins (standard robots.txt precedence)
        best_match_len = -1
        is_allowed = True  # Default: allowed if no rules match
        
        for allowed, rule_path in wildcard_rules:
            if path.startswith(rule_path) and len(rule_path) > best_match_len:
                best_match_len = len(rule_path)
                is_allowed = allowed
        
        return not is_allowed