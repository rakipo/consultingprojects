"""
Vector search functionality for MCP Vector Cypher Search.
"""

import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class VectorSearch:
    """Handles vector similarity search operations."""
    
    def __init__(self, config):
        """
        Initialize VectorSearch.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self._embedding_model: Optional[SentenceTransformer] = None
        self._neo4j_driver = None
    
    def get_embedding_model(self) -> SentenceTransformer:
        """Get or initialize the embedding model."""
        if self._embedding_model is None:
            logger.info(f"Loading SentenceTransformer model: {self.config.embedding_model_name}")
            self._embedding_model = SentenceTransformer(self.config.embedding_model_name)
            logger.info("SentenceTransformer model loaded")
        return self._embedding_model
    
    def get_neo4j_driver(self):
        """Get or initialize Neo4j driver."""
        if self._neo4j_driver is None:
            logger.info(f"Connecting to Neo4j at {self.config.neo4j_uri}")
            logger.info(f"Using username: {self.config.neo4j_user}")
            logger.info(f"Vector index: {self.config.vector_index_name}")
            self._neo4j_driver = GraphDatabase.driver(
                self.config.neo4j_uri, 
                auth=(self.config.neo4j_user, self.config.neo4j_password)
            )
            logger.info("Neo4j driver initialized")
        return self._neo4j_driver
    
    async def create_embedding(self, text: str) -> List[float]:
        """
        Create embedding for the given text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of embedding values
        """
        if not text or not text.strip():
            return []
        
        model = self.get_embedding_model()
        embedding = model.encode([text], convert_to_tensor=False)[0]
        
        if hasattr(embedding, "tolist"):
            return embedding.tolist()
        else:
            return list(embedding)
    
    async def search_similar_chunks(
        self, 
        query_embedding: List[float], 
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks in Neo4j using vector similarity.
        
        Args:
            query_embedding: The query embedding vector
            top_k: Number of top similar chunks to return (uses config default if None)
            
        Returns:
            List of similar chunks with their content and metadata
        """
        if not query_embedding:
            return []
        
        if top_k is None:
            top_k = self.config.top_k_chunks
        
        driver = self.get_neo4j_driver()
        
        # Vector similarity search query
        cypher_query = f"""
        CALL db.index.vector.queryNodes('{self.config.vector_index_name}', $top_k, $query_vector)
        YIELD node, score
        WHERE score >= $threshold
        RETURN node.chunk_text as content, 
               node.chunk_id as chunk_id,
               node.source_id as source_id,
               node.title as title,
               node.url as url,
               score
        ORDER BY score DESC
        """
        
        try:
            with driver.session() as session:
                result = session.run(
                    cypher_query,
                    query_vector=query_embedding,
                    top_k=top_k,
                    threshold=self.config.similarity_threshold
                )
                
                chunks = []
                for record in result:
                    chunks.append({
                        "content": record["content"],
                        "chunk_id": record["chunk_id"],
                        "source_id": record["source_id"],
                        "title": record["title"],
                        "url": record["url"],
                        "similarity_score": record["score"]
                    })
                
                logger.info(f"Found {len(chunks)} similar chunks")
                return chunks
                
        except Exception as e:
            logger.error(f"Error searching similar chunks: {e}")
            return []
    
    def should_use_vector_search(self, question: str) -> bool:
        """
        Determine if the question should use vector search.
        
        Args:
            question: The input question
            
        Returns:
            True if should use vector search, False otherwise
        """
        question_lower = question.lower()
        
        # Check if question contains "article"
        if "article" in question_lower:
            return True
        
        # Check if question has no specific label names
        # This is a simple heuristic - you might want to make this more sophisticated
        common_labels = ["user", "person", "company", "product", "order", "transaction", "node", "relationship"]
        has_label = any(label in question_lower for label in common_labels)
        
        # If no common labels found, assume it's a content/article search
        if not has_label:
            return True
        
        return False
    
    def close(self):
        """Close connections and cleanup resources."""
        if self._neo4j_driver:
            self._neo4j_driver.close()
            self._neo4j_driver = None