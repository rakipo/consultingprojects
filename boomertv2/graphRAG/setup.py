#!/usr/bin/env python3
"""
Setup script for GraphRAG Retrieval Agent.

This package provides a minimal GraphRAG (Graph Retrieval-Augmented Generation) 
system that combines vector similarity search with graph traversal for contextually 
rich information retrieval.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text() if (this_directory / "README.md").exists() else ""

# Read requirements
requirements_path = this_directory / "requirements.txt"
if requirements_path.exists():
    with open(requirements_path) as f:
        requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith('#')
        ]
else:
    requirements = [
        "sentence-transformers>=5.1.0",
        "neo4j>=5.28.1",
        "mcp>=1.12.3",
        "PyYAML>=6.0",
        "python-dotenv>=1.0.0",
    ]

setup(
    name="graphrag-retrieval-agent",
    version="1.0.0",
    author="GraphRAG Team",
    author_email="team@graphrag.example.com",
    description="Minimal GraphRAG retrieval system with Neo4j and MCP support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/graphrag-retrieval-agent",
    packages=find_packages(include=["modules", "modules.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "logging": [
            "structlog>=23.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "graphrag-cli=main:main",
            "graphrag-mcp=mcp_server:main",
            "graphrag-test=tests.test_runner:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.md"],
    },
    zip_safe=False,
    keywords=[
        "graphrag",
        "retrieval",
        "neo4j",
        "embeddings",
        "mcp",
        "knowledge-graph",
        "vector-search",
        "graph-traversal",
    ],
    project_urls={
        "Bug Reports": "https://github.com/example/graphrag-retrieval-agent/issues",
        "Source": "https://github.com/example/graphrag-retrieval-agent",
        "Documentation": "https://github.com/example/graphrag-retrieval-agent/wiki",
    },
)