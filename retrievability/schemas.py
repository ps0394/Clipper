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
    """Scoring output schema."""
    parseability_score: float  # 0-100
    failure_mode: str  # extraction-noisy | structure-missing | clean
    subscores: Dict[str, float]
    evidence_references: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


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