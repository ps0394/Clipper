"""Clipper - Standards-Based Access Gate Evaluation for Agent-Ready Content.

This package provides CLI tools to evaluate whether documentation pages are:
- Accessible and extractable by AI agents
- Structurally ready for AI agent content retrieval
- Optimized for retrieval systems using industry standards

Clipper evaluates 6 pillars (API-free):
- W3C Semantic HTML (25%)
- Content Extractability via Mozilla Readability (20%)
- Schema.org Structured Data (20%)
- DOM Navigability via WCAG 2.1 / axe-core (15%)
- Metadata Completeness via Dublin Core / OpenGraph (10%)
- HTTP Compliance via RFC 7231 (10%)
"""

__version__ = "3.0.0"