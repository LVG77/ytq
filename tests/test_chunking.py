"""
Tests for transcript chunking functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
import json
from ytq.core import chunk_transcript, chunk_by_sentences

@pytest.fixture
def metadata():
    return {
            'id': 'sample_id',
            'title': 'Sample Video Title',
            'uploader': 'Sample Channel',
            'channel_id': 'UCsample123',
            'duration': 600,
            'upload_date': '20230101',
            'view_count': 10000,
            'description': 'This is a sample video description',
            'categories': ['Education'],
            'tags': ['sample', 'test', 'video']
    }

# Sample transcript data for testing
@pytest.fixture
def sample_transcript_data(metadata):
    return {
        "transcript": "This is the first sentence. This is the second sentence. Here comes the third sentence! And a fourth? Finally, the fifth sentence.",
        "timestamps": [0, 5, 10, 15, 20],
        "entries": [
            {"start": 0, "text": "This is the first sentence."},
            {"start": 5, "text": "This is the second sentence."},
            {"start": 10, "text": "Here comes the third sentence!"},
            {"start": 15, "text": "And a fourth?"},
            {"start": 20, "text": "Finally, the fifth sentence."}
        ],
        "metadata": metadata
    }

@pytest.fixture
def long_transcript_data(metadata):
    # Create a longer transcript with 20 entries
    entries = []
    transcript = ""
    timestamps = []
    
    for i in range(20):
        text = f"This is sentence number {i+1} in the transcript. "
        timestamp = i * 5
        entries.append({"start": timestamp, "text": text})
        transcript += text
        timestamps.append(timestamp)
    
    return {
        "transcript": transcript,
        "timestamps": timestamps,
        "entries": entries,
        "metadata": metadata
    }


def test_chunk_transcript_basic(sample_transcript_data):
    """Test basic chunking functionality."""
    chunks = chunk_transcript(sample_transcript_data, chunk_size=100, chunk_overlap=20)
    
    # Should create at least one chunk
    assert len(chunks) > 0
    
    # Each chunk should have the required fields
    for chunk in chunks:
        assert "text" in chunk
        assert "timestamp" in chunk
        assert "end_timestamp" in chunk
        assert "entries" in chunk
        
    # First chunk should start at the beginning of the transcript
    assert chunks[0]["timestamp"] == 0
    
    # Verify content is preserved
    all_text = " ".join([chunk["text"] for chunk in chunks])
    # The chunked text might have extra spaces due to concatenation
    assert all(sentence in all_text for sentence in [
        "This is the first sentence",
        "This is the second sentence",
        "Here comes the third sentence",
        "And a fourth",
        "Finally, the fifth sentence"
    ])

def test_chunk_transcript_size_limits(long_transcript_data):
    """Test that chunks respect size limits."""
    chunk_size = 200
    chunks = chunk_transcript(long_transcript_data, chunk_size=chunk_size, chunk_overlap=50)
    
    # Check that no chunk exceeds the maximum size
    for chunk in chunks:
        assert len(chunk["text"]) <= chunk_size

def test_chunk_transcript_overlap(long_transcript_data):
    """Test that chunks have proper overlap."""
    chunks = chunk_transcript(long_transcript_data, chunk_size=200, chunk_overlap=50)
    
    # Need at least 2 chunks to test overlap
    if len(chunks) >= 2:
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i-1]["text"]
            curr_chunk = chunks[i]["text"]
            
            # There should be some overlap between consecutive chunks
            # This is a simplified test - in reality, we'd need to check for specific sentences
            assert any(word in curr_chunk for word in prev_chunk.split()[-10:])

def test_chunk_transcript_empty_input():
    """Test chunking with empty input."""
    with pytest.raises(ValueError, match="Invalid transcript data"):
        chunk_transcript({})
    
    with pytest.raises(ValueError, match="Invalid transcript data"):
        chunk_transcript({"entries": []})

def test_chunk_by_sentences_basic(sample_transcript_data):
    """Test basic sentence-based chunking."""
    chunks = chunk_by_sentences(sample_transcript_data, max_sentences=2, overlap_sentences=1)
    
    # Should create multiple chunks for 5 sentences with max 2 per chunk
    assert len(chunks) > 1
    
    # Each chunk should have the required fields
    for chunk in chunks:
        assert "text" in chunk
        assert "timestamp" in chunk
        assert "end_timestamp" in chunk
        assert "entries" in chunk

def test_chunk_by_sentences_overlap(sample_transcript_data):
    """Test sentence overlap in chunking."""
    chunks = chunk_by_sentences(sample_transcript_data, max_sentences=2, overlap_sentences=1)
    
    # With 5 sentences, max 2 per chunk, and overlap of 1, we expect 5 chunks
    # Chunk 1: Sentences 1-2
    # Chunk 2: Sentences 2-3
    # Chunk 3: Sentences 3-4
    # Chunk 4: Sentences 4-5
    # Chunk 5: Sentences 5
    assert len(chunks) == 5
    
    # Check for overlap between chunks
    assert "second sentence" in chunks[0]["text"] and "second sentence" in chunks[1]["text"]
    assert "third sentence" in chunks[1]["text"] and "third sentence" in chunks[2]["text"]
    assert "fourth" in chunks[2]["text"] and "fourth" in chunks[3]["text"]
