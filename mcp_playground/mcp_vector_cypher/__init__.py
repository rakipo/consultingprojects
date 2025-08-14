"""
MCP Vector Cypher Search Module

A Python module that provides vector similarity search combined with Cypher query generation
for Neo4j databases. Designed to work as an MCP (Model Context Protocol) server.
"""

from .server import MCPVectorCypherServer
from .config import Config
from .search import VectorSearch
from .cypher import CypherGenerator

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = [
    "MCPVectorCypherServer",
    "Config", 
    "VectorSearch",
    "CypherGenerator"
]