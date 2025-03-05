"""
Tests for embedding generation functionality.
"""
import os
import pytest
import json
from pydantic import BaseModel
from unittest.mock import patch, MagicMock

from ytq.embeddings import (
    generate_embeddings, 
    VoyageaiEmbedding, 
    OpenAIEmbedding
)

@pytest.fixture
def sample_transcript_chunks():
    return [
        {
            "text": "This is the first chunk of text.",
            "timestamp": 0,
            "end_timestamp": 5,
            "entries": [{"start": 0, "text": "This is the first chunk of text."}]
        },
        {
            "text": "This is the second chunk with more content.",
            "timestamp": 5,
            "end_timestamp": 10,
            "entries": [{"start": 5, "text": "This is the second chunk with more content."}]
        },
        {
            "text": "Here is a third chunk to process.",
            "timestamp": 10,
            "end_timestamp": 15,
            "entries": [{"start": 10, "text": "Here is a third chunk to process."}]
        }
    ]

def test_generate_embeddings_empty_input():
    """Test embedding generation with empty input."""
    result = generate_embeddings([])
    assert result == []

@patch('requests.post')
def test_voyage_embedding(mock_post, sample_transcript_chunks):
    """Test VoyageEmbedding provider with mocked API response."""
    # Mock the VoyageAI API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"embedding": [0.1, 0.2, 0.3], 'index': 0},
            {"embedding": [0.4, 0.5, 0.6], 'index': 1},
            {"embedding": [0.7, 0.8, 0.9], 'index': 2}
        ]
    }
    mock_post.return_value = mock_response
    
    # Set dummy API key for test
    os.environ["VOYAGE_API_KEY"] = "test_key"
    
    result = generate_embeddings(sample_transcript_chunks, provider="voyage")
    
    # Verify API was called with expected parameters
    mock_post.assert_called_once()
    call_args = mock_post.call_args[1]
    assert "model" in call_args["json"]
    assert "input" in call_args["json"]
    assert len(call_args["json"]["input"]) == 3  # Three texts
    
    # Check results have expected embeddings
    assert result[0]['embedding'] == [0.1, 0.2, 0.3]
    assert result[1]["embedding"] == [0.4, 0.5, 0.6]
    assert result[2]["embedding"] == [0.7, 0.8, 0.9]

@patch('openai.OpenAI')
def test_openai_embedding(mock_openai_client, sample_transcript_chunks):
    """Test OpenAIEmbedding provider with mocked API response."""
    # Create mock client and response
    mock_client = MagicMock()
    mock_openai_client.return_value = mock_client
    
    # Mock the embeddings.create method
    mock_response = MagicMock()
    mock_client.embeddings.create.return_value = mock_response
    
    # Setup mock data objects with embedding results
    class MockEmbeddingData:
        def __init__(self, idx, embedding):
            self.index = idx
            self.embedding = embedding
    
    # Set up the response data
    mock_response.data = [
        MockEmbeddingData(0, [0.1, 0.2, 0.3]),
        MockEmbeddingData(1, [0.4, 0.5, 0.6]),
        MockEmbeddingData(2, [0.7, 0.8, 0.9])
    ]
    
    # Set dummy API key for test
    os.environ["OPENAI_API_KEY"] = "test_key"
    
    result = generate_embeddings(sample_transcript_chunks, provider="openai")
    
    # Verify client was created and API method called with expected parameters
    mock_openai_client.assert_called_once()
    mock_client.embeddings.create.assert_called_once()
    call_args = mock_client.embeddings.create.call_args[1]
    assert "model" in call_args
    assert "input" in call_args
    assert len(call_args["input"]) == 3  # Three texts
    
    # Check results have expected embeddings
    assert result[0]["embedding"] == [0.1, 0.2, 0.3]
    assert result[1]["embedding"] == [0.4, 0.5, 0.6]
    assert result[2]["embedding"] == [0.7, 0.8, 0.9]

@patch('openai.OpenAI')
def test_openai_embedding_with_out_of_order_response(mock_openai_client, sample_transcript_chunks):
    """Test OpenAIEmbedding provider with out-of-order API response."""
    # Create mock client and response
    mock_client = MagicMock()
    mock_openai_client.return_value = mock_client
    
    # Mock the embeddings.create method
    mock_response = MagicMock()
    mock_client.embeddings.create.return_value = mock_response
    
    # Setup mock data objects with embedding results - out of order
    class MockEmbeddingData:
        def __init__(self, idx, embedding):
            self.index = idx
            self.embedding = embedding
    
    # Set up the response data - intentionally out of order
    mock_response.data = [
        MockEmbeddingData(2, [0.7, 0.8, 0.9]),  # Third chunk
        MockEmbeddingData(0, [0.1, 0.2, 0.3]),  # First chunk
        MockEmbeddingData(1, [0.4, 0.5, 0.6])   # Second chunk
    ]
    
    # Set dummy API key for test
    os.environ["OPENAI_API_KEY"] = "test_key"
    
    result = generate_embeddings(sample_transcript_chunks, provider="openai")
    
    # Check results have expected embeddings in the correct order
    assert result[0]["embedding"] == [0.1, 0.2, 0.3]
    assert result[1]["embedding"] == [0.4, 0.5, 0.6]
    assert result[2]["embedding"] == [0.7, 0.8, 0.9]

@patch('openai.OpenAI')
def test_batch_processing(mock_openai_client):
    """Test batch processing of chunks."""
    # Create a larger set of chunks to test batching
    many_chunks = []
    for i in range(25):  # More than the default batch size of 20
        many_chunks.append({
            "text": f"This is test chunk {i}",
            "timestamp": i,
            "end_timestamp": i + 1,
            "entries": [{"start": i, "text": f"This is test chunk {i}"}]
        })
    
    # Create mock client and response
    mock_client = MagicMock()
    mock_openai_client.return_value = mock_client
    
    # Mock the embeddings.create method to handle multiple batches
    def side_effect_function(model, input):
        # Create a mock response for each batch
        class MockEmbeddingData:
            def __init__(self, idx, embedding):
                self.index = idx
                self.embedding = embedding
        
        mock_response = MagicMock()
        mock_response.data = [
            MockEmbeddingData(i, [0.1 * i, 0.2 * i, 0.3 * i]) 
            for i in range(len(input))
        ]
        return mock_response
    
    mock_client.embeddings.create.side_effect = side_effect_function
    
    # Set dummy API key for test
    os.environ["OPENAI_API_KEY"] = "test_key"
    
    # Use openai provider with a small batch size
    result = generate_embeddings(many_chunks, provider="openai", batch_size=10)
    
    # Check that all chunks were processed
    assert len(result) == 25
    for i, chunk in enumerate(result):
        assert "embedding" in chunk
        assert chunk["embedding"] is not None
    
    # Verify that the client was called multiple times (3 batches for 25 items with batch_size=10)
    assert mock_client.embeddings.create.call_count == 3

def test_custom_embedding_provider(sample_transcript_chunks):
    """Test using a custom embedding provider instance."""
    # Create a custom provider that returns fixed embeddings
    class CustomProvider:
        def generate(self, texts):
            return [[1.0, 2.0, 3.0] for _ in texts]
    
    provider = CustomProvider()
    result = generate_embeddings(sample_transcript_chunks, provider=provider)
    
    # Check that all chunks have the custom embeddings
    for chunk in result:
        assert chunk["embedding"] == [1.0, 2.0, 3.0]

def test_unknown_provider():
    """Test error handling for unknown provider."""
    with pytest.raises(ValueError, match="Unknown embedding provider"):
        generate_embeddings([{"text": "test"}], provider="unknown_provider")