"""JSON output contracts and data schemas for retrievability evaluation."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json


@dataclass
class CrawlResult:
    """Per-URL crawl output schema."""
    url: str
    timestamp: str
    status: int
    headers: Dict[str, str]
    html_path: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass  
class ParseSignals:
    """Raw parseability signals extracted from HTML."""
    has_main_element: bool
    has_article_element: bool
    heading_hierarchy_valid: bool
    text_density_ratio: float
    code_blocks_count: int
    tables_count: int
    boilerplate_leakage_estimate: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ParseResult:
    """Per-page parse output schema.""" 
    html_path: str
    signals: ParseSignals
    evidence: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['signals'] = self.signals.to_dict()
        return result


@dataclass
class ScoreResult:
    """Clipper Standards-Based Scoring Output Schema."""
    parseability_score: float              # 0-100 final Access Gate score
    failure_mode: str                      # Standards-based failure classification
    html_path: str                         # Source HTML file path
    url: str                              # Evaluated URL
    component_scores: Dict[str, float]     # Individual component scores (WCAG, HTML5, etc.)
    audit_trail: Dict[str, Any]           # Detailed evaluation evidence and methodology
    standards_authority: Dict[str, str]    # Standards authority mapping for each component
    evaluation_methodology: str           # Clipper methodology identifier
    
    # Backward compatibility
    subscores: Optional[Dict[str, float]] = None
    evidence_references: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        # Ensure component_scores are included in subscores for backward compatibility
        if not self.subscores:
            result['subscores'] = self.component_scores
        return result


@dataclass
class ReportResult:
    """Final report schema combining all stages."""
    url: str
    crawl_result: CrawlResult
    parse_result: ParseResult
    score_result: ScoreResult
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'url': self.url,
            'crawl_result': self.crawl_result.to_dict(),
            'parse_result': self.parse_result.to_dict(), 
            'score_result': self.score_result.to_dict()
        }


@dataclass
class FormatResponse:
    """Single format response in content negotiation testing."""
    accept_header: str
    content_type: str
    content_length: int
    status_code: int
    content_hash: str  # MD5 hash to detect identical content across formats
    html_path: str     # Where content is saved (relative to snapshots dir)
    response_time_ms: int  # Response time for performance comparison
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass 
class ContentNegotiationResult:
    """Content negotiation test results for a single URL."""
    url: str
    timestamp: str
    baseline_format: FormatResponse      # HTML request (text/html)
    alternative_formats: List[FormatResponse]  # Other Accept header tests
    format_availability_score: float    # 0-100 based on available alternatives
    content_consistency_score: float    # Are different formats actually different?
    agent_optimization_detected: bool   # True if site appears agent-optimized
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'url': self.url,
            'timestamp': self.timestamp,
            'baseline_format': self.baseline_format.to_dict(),
            'alternative_formats': [fmt.to_dict() for fmt in self.alternative_formats],
            'format_availability_score': self.format_availability_score,
            'content_consistency_score': self.content_consistency_score,
            'agent_optimization_detected': self.agent_optimization_detected
        }