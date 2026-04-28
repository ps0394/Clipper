"""JSON output contracts and data schemas for retrievability evaluation."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
import json


@dataclass
class RedirectStep:
    """Individual redirect step in chain."""
    from_url: str
    to_url: str
    status_code: int
    redirect_time_ms: float
    headers: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CrawlResult:
    """Per-URL crawl output schema with redirect chain tracking."""
    url: str
    timestamp: str
    status: int
    headers: Dict[str, str]
    html_path: str
    
    # Redirect chain tracking (Phase 1 enhancement)
    redirect_chain: List[RedirectStep] = field(default_factory=list)
    redirect_count: int = 0
    total_redirect_time_ms: float = 0.0
    final_response_time_ms: float = 0.0
    final_url: str = ""  # URL after all redirects
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['redirect_chain'] = [step.to_dict() for step in self.redirect_chain]
        return result


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
    agent_content_hints: Dict[str, Any] = field(default_factory=dict)
    
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
    """Clipper Standards-Based Scoring Output Schema.

    A successful run populates every pillar in ``component_scores`` and leaves
    ``partial_evaluation`` False. If one or more pillars fail catastrophically
    (network timeout, parser crash, etc.) the orchestrator drops those pillars
    from the weighted average, lists them in ``failed_pillars``, and sets
    ``partial_evaluation=True``. Downstream tooling should treat partial
    results as structurally honest: the surviving pillars are real
    measurements, not padded with zeros.
    """
    parseability_score: float              # 0-100 final Access Gate score (renormalized over surviving pillars)
    failure_mode: str                      # Standards-based failure classification
    html_path: str                         # Source HTML file path
    url: str                              # Evaluated URL
    component_scores: Dict[str, float]     # Individual pillar scores. Missing keys = pillar failed.
    audit_trail: Dict[str, Any]           # Detailed evaluation evidence and methodology
    standards_authority: Dict[str, str]    # Standards authority mapping for each component
    evaluation_methodology: str           # Clipper methodology identifier

    # Failure-mode transparency (Phase 0.2)
    partial_evaluation: bool = False       # True when one or more pillars could not be evaluated
    failed_pillars: List[str] = field(default_factory=list)  # Pillars excluded from the final score

    # Content-type-aware scoring (Phase 1.1)
    content_type: str = 'article'          # Detected profile (article/landing/reference/sample/faq/tutorial)
    universal_score: Optional[float] = None  # Same component scores under default (article) weights

    # Rendering-mode dimension (Phase 3.1)
    render_mode: str = 'rendered'          # 'raw' | 'rendered' — which fetch path produced the HTML evaluated

    # v2 evidence disclosure (Phase 6 Session 2)
    # The v2 headline score ships as "evidence-partial": it is calibrated
    # against corpus-002 (n=43, single grader architecture, one corpus
    # snapshot, no held-out validation). This block exposes the corpus-002
    # r and the evidence tier so downstream tooling can surface CI-style
    # qualifiers without re-reading the findings doc.
    confidence_range: Optional[Dict[str, Any]] = None

    # Backward compatibility
    subscores: Optional[Dict[str, float]] = None
    evidence_references: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        # Ensure component_scores are included in subscores for backward compatibility
        if not self.subscores:
            result['subscores'] = self.component_scores
        return result


# ---------------------------------------------------------------------------
# v2.1 — Methodology disclosure (always-on) + diagnostic-mode composite null
# ---------------------------------------------------------------------------
#
# Sessions 8 / 9 / 9.5 (April 2026) established that the v2-evidence-partial
# composite (`parseability_score` / `universal_score`) was calibrated on
# corpus-002 and does not generalize to the held-out corpus-003 set
# (Pearson r vs judged QA accuracy ≈ +0.10 against ship gate r ≥ +0.35).
#
# Per-pillar measurements are still real signals against published standards
# and remain populated in `component_scores`. v2.1 surfaces this status
# directly in the score JSON so tools parsing the output cannot miss it.
#
# See findings/post-v2-roadmap.md and findings/v2.1-release-scope.md.

V2_1_METHODOLOGY_DISCLOSURE: Dict[str, Any] = {
    "scoring_version": "v2-evidence-partial",
    "calibration_corpus": "corpus-002",
    "generalization_status": (
        "fails on corpus-003 (Pearson r ≈ +0.10 vs ship gate +0.35); "
        "see findings/post-v2-roadmap.md"
    ),
    "recommended_use": "pillar-level diagnostics; not validated for ranking pages against each other",
    "release": "v2.1",
}


def apply_methodology_disclosure(
    results: List[Dict[str, Any]],
    diagnostic_mode: bool = False,
) -> List[Dict[str, Any]]:
    """Annotate each ScoreResult dict with the v2.1 methodology block.

    When ``diagnostic_mode`` is True, the composite headline scores
    (``parseability_score`` and ``universal_score``) are set to None and a
    ``diagnostic_mode: True`` marker is added. Component (pillar) scores
    remain populated — those are the measurements that did not fail to
    generalize. ``methodology`` is added in both modes; the only thing
    ``--diagnostic-mode`` toggles is whether the composite numbers are
    reported.

    This function mutates and returns the list it was given.
    """
    for result in results:
        result["methodology"] = dict(V2_1_METHODOLOGY_DISCLOSURE)
        result["diagnostic_mode"] = bool(diagnostic_mode)
        if diagnostic_mode:
            result["parseability_score"] = None
            result["universal_score"] = None
    return results


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