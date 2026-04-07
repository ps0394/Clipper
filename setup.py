"""Setup script for retrievability evaluation system."""

from setuptools import setup, find_packages

setup(
    name="retrievability-eval",
    version="0.1.0",
    description="CLI tool for evaluating documentation page retrievability",
    packages=find_packages(),
    install_requires=[
        "beautifulsoup4>=4.9.0",
        "requests>=2.25.0"
    ],
    entry_points={
        "console_scripts": [
            "retrievability=retrievability.cli:main"
        ]
    },
    python_requires=">=3.7"
)