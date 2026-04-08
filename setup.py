"""Setup script for YARA 2.0 (Yet Another Retrieval Analyzer).

YARA 2.0 provides hybrid agent-ready documentation assessment combining:
- Google Lighthouse accessibility, SEO, and performance metrics (70%)
- Enhanced content analysis and structure evaluation (20%)
- Direct AI agent extraction simulation (10%)
"""

from setuptools import setup, find_packages

setup(
    name="yara-retrieval-eval",
    version="2.0.0",
    description="YARA 2.0: Hybrid scoring for agent-ready documentation assessment",
    long_description="YARA 2.0 combines Google Lighthouse with content analysis and agent performance simulation for accurate documentation quality evaluation.",
    packages=find_packages(),
    install_requires=[
        "beautifulsoup4>=4.9.0",
        "requests>=2.25.0"
    ],
    entry_points={
        "console_scripts": [
            "yara=retrievability.cli:main",
            "retrievability=retrievability.cli:main"
        ]
    },
    python_requires=">=3.7",
    keywords="documentation ai agents retrieval lighthouse accessibility",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers", 
        "Topic :: Documentation",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11"
    ]
)