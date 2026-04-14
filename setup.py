"""Setup script for Clipper - Standards-Based Access Gate Evaluation.

Clipper provides API-free, standards-based evaluation for agent-ready content using:
- WCAG 2.1 Accessibility (Deque axe-core) - 25%
- W3C Semantic HTML Analysis - 25%  
- Schema.org Structured Data - 20%
- HTTP Standards Compliance (RFC 7231) - 15%
- Agent-Focused Content Quality - 15%
"""

from setuptools import setup, find_packages

setup(
    name="clipper-retrieval-eval",
    version="3.0.0",
    description="Clipper: Standards-based access gate evaluation for agent-ready content",
    long_description="Clipper evaluates content accessibility for AI agents using established industry standards (WCAG, W3C, Schema.org, RFC 7231). Completely API-free with full audit traceability.",
    packages=find_packages(),
    install_requires=[
        "axe-selenium-python>=2.1.6",  # WCAG 2.1 accessibility evaluation
        "selenium>=4.0.0",              # WebDriver for browser automation
        "beautifulsoup4>=4.9.0",        # HTML parsing and analysis
        "lxml>=4.9.0",                  # High-performance XML/HTML parser
        "html5lib>=1.1",                # W3C-compliant HTML5 parser
        "extruct>=0.13.0",              # Schema.org structured data extraction
        "httpx>=0.24.0",                # Modern HTTP client for standards compliance
        "pyquery>=1.4.0",               # jQuery-style HTML manipulation
        "advertools>=0.13.0",           # SEO and content analysis framework
        "charset-normalizer>=3.0.0",    # Character encoding detection
        "jsonschema>=4.0.0",            # JSON Schema validation
        "requests>=2.25.0"              # HTTP library fallback
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "black>=21.0.0",
            "flake8>=3.8.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "clipper=retrievability.cli:main",
            "retrievability=retrievability.cli:main"
        ]
    },
    python_requires=">=3.8",
    keywords="documentation ai agents retrieval standards accessibility wcag schema.org",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers", 
        "Intended Audience :: Information Technology",
        "Topic :: Documentation",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12"
    ]
)