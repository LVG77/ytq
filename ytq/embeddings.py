import os
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmbeddingProvider:
    """Base class for embedding providers"""
    def generate(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts"""
        raise NotImplementedError("Subclasses must implement generate()")

class VoyageaiEmbedding(EmbeddingProvider):
    """VoyageAI embedding API implementation"""
    def __init__(self, api_key: str = None, model: str = "voyage-3-lite"):
        self.api_key = api_key or os.getenv("VOYAGE_API_KEY")
        if not self.api_key:
            raise ValueError("VoyageAI API key is required. Set VOYAGE_API_KEY env variable or pass as api_key")
        self.model = model
        self.api_url = "https://api.voyageai.com/v1/embeddings"

    def generate(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using VoyageAI API"""
        try:
            headers = {
                "content-type": "application/json",
                "authorization": f"Bearer {self.api_key}"
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json={"model": self.model, "input": texts, "input_type": "document"}
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Sort embeddings by index to match input order
            embeddings = sorted(result["data"], key=lambda x: x["index"])
            # Extract embeddings from response
            return [item["embedding"] for item in embeddings]
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling VoyageAI API: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise RuntimeError(f"VoyageAI API error: {str(e)}")

class OpenAIEmbedding(EmbeddingProvider):
    """OpenAI embedding API implementation"""
    def __init__(self, api_key: str = None, model: str = "text-embedding-3-small"):
        import openai
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY env variable or pass as api_key")
        self.model = model
        self.client = openai.OpenAI()

    def generate(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using OpenAI API"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            
            idx = [item.index for item in response.data]
            embeddings = [emb.embedding for emb in response.data]
            embeddings_sorted = [emb for _, emb in sorted(zip(idx, embeddings))]
            return embeddings_sorted
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise RuntimeError(f"OpenAI API error: {str(e)}")

def get_embedding_provider(provider: str = "openai", **kwargs) -> EmbeddingProvider:
    """Factory function to get an embedding provider"""
    if provider.lower() == "voyage":
        return VoyageaiEmbedding(**kwargs)
    elif provider.lower() == "openai":
        return OpenAIEmbedding(**kwargs)
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")

def generate_embeddings(
    transcript_chunks: list[dict[str, any]], 
    provider: str | EmbeddingProvider = "openai",
    batch_size: int = 100,
    **kwargs
) -> list[dict[str, any]]:
    """
    Generate embeddings for each transcript text chunk.
    
    Args:
        transcript_chunks: List of transcript chunks
        provider: String name of provider ('openai', 'voyage') or an EmbeddingProvider instance
        batch_size: Number of texts to process in a single API call
        **kwargs: Additional arguments to pass to the embedding provider
        
    Returns:
        The input transcript chunks list with embeddings added
    """
    if not transcript_chunks:
        return []
    
    # Get the embedding provider
    if isinstance(provider, str):
        embedding_provider = get_embedding_provider(provider, **kwargs)
    else:
        embedding_provider = provider
    
    # Process chunks in batches to avoid API limits
    result_chunks = []
    
    for i in range(0, len(transcript_chunks), batch_size):
        batch = transcript_chunks[i:i+batch_size]
        texts = [chunk["text"] for chunk in batch]
        
        try:
            # Generate embeddings for the batch
            embeddings = embedding_provider.generate(texts)
            
            # Add embeddings to the chunks
            for j, embedding in enumerate(embeddings):
                chunk_with_embedding = batch[j].copy()
                chunk_with_embedding["embedding"] = embedding
                result_chunks.append(chunk_with_embedding)
        
        except Exception as e:
            logger.error(f"Error generating embeddings for batch {i//batch_size}: {str(e)}")
            # Add the chunks without embeddings, but with an error flag
            for chunk in batch:
                chunk_with_error = chunk.copy()
                chunk_with_error["embedding"] = None
                chunk_with_error["embedding_error"] = str(e)
                result_chunks.append(chunk_with_error)
    
    return result_chunks

def get_query_embedding(query: str, provider: str | EmbeddingProvider = "openai", **kwargs) -> list[float]:
    """
    Get the embedding for a query.

    Args:
        query: The query string
        provider: String name of provider ('openai', 'voyage') or an EmbeddingProvider instance
        **kwargs: Additional arguments to pass to the embedding provider
        Returns:
        The embedding for the query
    """
    if isinstance(provider, str):
        embedding_provider = get_embedding_provider(provider, **kwargs)
    else:
        embedding_provider = provider
    
    try:
        return embedding_provider.generate([query])[0]

    except Exception as e:
        logger.error(f"Error generating embedding for query: {str(e)}")
        raise RuntimeError(f"Error generating embedding for query: {str(e)}")