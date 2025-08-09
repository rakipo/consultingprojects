#!/usr/bin/env python3
"""
boomer-vector-embedding-creator
A custom MCP server that exposes a tool to generate vector embeddings
for a given input string using SentenceTransformer('all-MiniLM-L6-v2').

This server communicates over stdio per the Model Context Protocol (MCP).
"""

import asyncio
import logging
from typing import Dict, Any, List

from sentence_transformers import SentenceTransformer

try:
    # MCP Python SDK
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "mcp package is required. Install with `pip install mcp`."
    ) from e


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s",
)
logger = logging.getLogger("boomer-vector-embedding-creator")


SERVER_NAME = "boomer-vector-embedding-creator"
_embedding_model: SentenceTransformer | None = None


def _get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading SentenceTransformer model: all-MiniLM-L6-v2")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("SentenceTransformer model loaded")
    return _embedding_model


server = Server(SERVER_NAME)


@server.tool()
async def create_embedding(text: str) -> Dict[str, Any]:
    """Create a vector embedding for the provided text.

    Args:
        text: The input text to embed

    Returns:
        A dictionary containing the embedding vector and metadata.
    """
    if text is None or len(text.strip()) == 0:
        return {
            "embedding": [],
            "model": "all-MiniLM-L6-v2",
            "dimension": 0,
            "error": "Input text is empty",
        }

    model = _get_embedding_model()
    embedding = model.encode([text], convert_to_tensor=False)[0]

    if hasattr(embedding, "tolist"):
        embedding_list: List[float] = embedding.tolist()
    else:
        embedding_list = list(embedding)

    return {
        "embedding": embedding_list,
        "model": "all-MiniLM-L6-v2",
        "dimension": len(embedding_list),
    }


async def _main() -> None:
    logger.info("Starting MCP stdio server: %s", SERVER_NAME)
    async with stdio_server() as (read_stream, write_stream):
        await server.serve(read_stream, write_stream)


if __name__ == "__main__":
    asyncio.run(_main()) 