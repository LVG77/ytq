"""
Tests for the database operations.
"""
import pytest
import sqlite3
import pathlib
import tempfile
from unittest.mock import patch, MagicMock
from ytq import db

@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir) / "test.db"
        with patch('ytq.db.get_db_path', return_value=temp_path):
            db.init_db()
            yield temp_path

@pytest.fixture
def sample_video_data():
    """Sample video data for testing."""
    return {
        'metadata': {
            'video_id': 'test123',
            'url': 'https://youtube.com/watch?v=test123',
            'title': 'Test Video',
            'author': 'Test Channel',
            'duration': 600,
            'view_count': 1000,
            'upload_date': '20240101',
            'description': 'This is a test video'
        },
        'transcript': 'This is a test transcript for the video.'
    }

@pytest.fixture
def sample_summary():
    """Sample summary data for testing."""
    return {
        'summary': 'This is a summary of the test video.',
        'tldr': 'A test video about testing.',
        'tags': ['test', 'video', 'python']
    }

@pytest.fixture
def sample_chunks():
    """Sample chunks data for testing."""
    return [
        {
            'text': 'This is chunk one of the test video.',
            'timestamp': 0.0,
            'end_timestamp': 10.0,
            'embedding': [0.1, 0.2, 0.3, 0.4, 0.5],
            'entries': [
                {'start': 0.0, 'text': 'This is chunk one of the test video.'}
            ]
        },
        {
            'text': 'This is chunk two of the test video.',
            'timestamp': 10.0,
            'end_timestamp': 20.0,
            'embedding': [0.2, 0.3, 0.4, 0.5, 0.6],
            'entries': [
                {'start': 10.0, 'text': 'This is chunk two of the test video.'}
            ]
        }
    ]

def test_init_db(temp_db):
    """Test database initialization."""
    # Check if tables were created
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # Check videos table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='videos'")
    assert cursor.fetchone() is not None
    
    # Check video_details table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='video_details'")
    assert cursor.fetchone() is not None
    
    # Check FTS5 tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='videos_fts'")
    assert cursor.fetchone() is not None
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='video_details_fts'")
    assert cursor.fetchone() is not None
    
    # Check triggers
    cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name='videos_ai'")
    assert cursor.fetchone() is not None
    
    conn.close()

def test_encode_decode():
    """Test encoding and decoding of embeddings."""
    original = [0.1, 0.2, 0.3, 0.4, 0.5]
    encoded = db.encode(original)
    decoded = db.decode(encoded)
    
    # Check that the values are approximately equal (floating point precision issues)
    assert len(original) == len(decoded)
    for o, d in zip(original, decoded):
        assert abs(o - d) < 1e-6

def test_store_and_get_video(temp_db, sample_video_data, sample_summary, sample_chunks):
    """Test storing and retrieving a video."""
    # Store the video
    db.store_video(sample_video_data, sample_summary, sample_chunks)
    
    # Retrieve the video
    video = db.get_video('test123')
    
    # Check video metadata
    assert video is not None
    assert video['video_id'] == 'test123'
    assert video['title'] == 'Test Video'
    assert video['author'] == 'Test Channel'
    assert video['summary'] == 'This is a summary of the test video.'
    assert video['tldr'] == 'A test video about testing.'
    assert video['tags'] == ['test', 'video', 'python']
    
    # Check chunks
    assert 'chunks' in video
    assert len(video['chunks']) == 2
    assert video['chunks'][0]['chunk_text'] == 'This is chunk one of the test video.'
    assert video['chunks'][1]['chunk_text'] == 'This is chunk two of the test video.'

def test_update_video(temp_db, sample_video_data, sample_summary, sample_chunks):
    """Test updating an existing video."""
    # Store the video
    db.store_video(sample_video_data, sample_summary, sample_chunks)
    
    # Update video data
    updated_data = sample_video_data.copy()
    updated_data['metadata']['title'] = 'Updated Test Video'
    
    updated_summary = sample_summary.copy()
    updated_summary['summary'] = 'This is an updated summary with keyword improvement'
    updated_sample_chunks = sample_chunks.copy()
    updated_sample_chunks[0]['text'] = 'Updated chunk one, with keyword improvement'
    
    # Store the updated video
    db.store_video(updated_data, updated_summary, updated_sample_chunks)

    # Retrieve the video
    video = db.get_video('test123')
    
    # Check updated fields
    assert video['title'] == 'Updated Test Video'
    assert video['summary'] == 'This is an updated summary with keyword improvement'

    # Search for videos
    results = db.search_videos('improvement')
    assert len(results) >= 1
    assert results[0]['video_id'] == 'test123'
    results = db.search_chunks('improvement')
    assert len(results) >= 1
    assert results[0]['video_id'] == 'test123'

def test_get_video_chunks(temp_db, sample_video_data, sample_summary, sample_chunks):
    """Test retrieving chunks for a video."""
    # Store the video
    db.store_video(sample_video_data, sample_summary, sample_chunks)
    
    # Retrieve chunks without embeddings
    chunks = db.get_video_chunks('test123')
    assert len(chunks) == 2
    assert 'embedding' not in chunks[0]
    
    # Retrieve chunks with embeddings
    chunks_with_embeddings = db.get_video_chunks('test123', with_embeddings=True)
    assert len(chunks_with_embeddings) == 2
    assert 'embedding' in chunks_with_embeddings[0]
    assert isinstance(chunks_with_embeddings[0]['embedding'], list)
    assert len(chunks_with_embeddings[0]['embedding']) == 5

def test_search_videos(temp_db, sample_video_data, sample_summary, sample_chunks):
    """Test searching for videos."""
    # Store the video
    db.store_video(sample_video_data, sample_summary, sample_chunks)
    
    # Search for videos
    results = db.search_videos('test')
    assert len(results) >= 1
    assert results[0]['video_id'] == 'test123'
    
    # Search for non-existent content
    results = db.search_videos('nonexistent')
    assert len(results) == 0

def test_search_chunks(temp_db, sample_video_data, sample_summary, sample_chunks):
    """Test searching for chunks."""
    # Store the video
    db.store_video(sample_video_data, sample_summary, sample_chunks)
    
    # Search for chunks
    results = db.search_chunks('chunk one')
    assert len(results) >= 1
    assert 'chunk one' in results[0]['chunk_text']
    
    # Search for non-existent content
    results = db.search_chunks('nonexistent')
    assert len(results) == 0

def test_get_all_videos(temp_db, sample_video_data, sample_summary, sample_chunks):
    """Test retrieving all videos."""
    # Store the video
    db.store_video(sample_video_data, sample_summary, sample_chunks)
    
    # Create a second video
    second_video = sample_video_data.copy()
    second_video['metadata']['video_id'] = 'test456'
    second_video['metadata']['title'] = 'Second Test Video'
    db.store_video(second_video, sample_summary, sample_chunks)
    
    # Retrieve all videos
    videos = db.get_all_videos()
    assert len(videos) == 2
    
    # Test pagination
    limited_videos = db.get_all_videos(limit=1)
    assert len(limited_videos) == 1
    
    offset_videos = db.get_all_videos(offset=1, limit=1)
    assert len(offset_videos) == 1
    assert offset_videos[0]['video_id'] != limited_videos[0]['video_id']

def test_delete_video(temp_db, sample_video_data, sample_summary, sample_chunks):
    """Test deleting a video."""
    # Store the video
    db.store_video(sample_video_data, sample_summary, sample_chunks)
    
    # Delete the video
    result = db.delete_video('test123')
    assert result is True
    
    # Verify the video is deleted
    video = db.get_video('test123')
    assert video is None
    
    # Verify no chunks remain
    chunks = db.get_video_chunks('test123')
    assert len(chunks) == 0
    
    # Test deleting non-existent video
    result = db.delete_video('nonexistent')
    assert result is False

def test_find_similar_chunks(temp_db, sample_video_data, sample_summary, sample_chunks):
    """Test finding chunks with similar embeddings."""
    # Store the video with sample chunks that have embeddings
    db.store_video(sample_video_data, sample_summary, sample_chunks)
    
    # Create a second video with different embeddings
    second_video = sample_video_data.copy()
    second_video['metadata']['video_id'] = 'test456'
    second_video['metadata']['title'] = 'Second Test Video'
    
    second_chunks = [
        {
            'text': 'This is a completely different topic.',
            'timestamp': 0.0,
            'end_timestamp': 10.0,
            'embedding': [0.9, 0.8, 0.7, 0.6, 0.5],  # Very different embedding
            'entries': [{'start': 0.0, 'text': 'This is a completely different topic.'}]
        },
        {
            'text': 'This is slightly similar to the first video.',
            'timestamp': 10.0,
            'end_timestamp': 20.0,
            'embedding': [0.25, 0.35, 0.45, 0.55, 0.65],  # Somewhat similar to first video
            'entries': [{'start': 10.0, 'text': 'This is slightly similar to the first video.'}]
        }
    ]
    
    db.store_video(second_video, sample_summary, second_chunks)
    
    # Create a third video
    third_video = sample_video_data.copy()
    third_video['metadata']['video_id'] = 'test789'
    third_video['metadata']['title'] = 'Third Test Video'
    
    third_chunks = [
        {
            'text': 'This is from the third video.',
            'timestamp': 0.0,
            'end_timestamp': 10.0,
            'embedding': [0.1, 0.3, 0.5, 0.7, 0.9],  # Different embedding
            'entries': [{'start': 0.0, 'text': 'This is from the third video.'}]
        }
    ]
    
    db.store_video(third_video, sample_summary, third_chunks)
    
    # Query embedding similar to first video's first chunk
    query_embedding = [0.15, 0.25, 0.35, 0.45, 0.55]  # Closer to first video's embeddings
    
    # Test general search (all videos)
    results = db.find_similar_chunks(query_embedding, limit=5)
    
    # We should get at least 3 results (one from each video)
    assert len(results) >= 3
    
    # Test that results are sorted by similarity (highest first)
    for i in range(len(results) - 1):
        assert results[i]['similarity'] >= results[i + 1]['similarity']
    
    # Test search restricted to specific videos (first and third)
    specific_results = db.find_similar_chunks(
        query_embedding, 
        limit=5, 
        video_ids=['test123', 'test789']
    )
    
    # All results should be from the specified videos
    for result in specific_results:
        assert result['video_id'] in ['test123', 'test789']
        assert result['video_id'] != 'test456'  # Should not include second video
    
    # Test with a single video ID in the list
    single_video_results = db.find_similar_chunks(
        query_embedding,
        limit=5,
        video_ids=['test456']
    )
    
    # All results should be from the second video
    for result in single_video_results:
        assert result['video_id'] == 'test456'
    
    # Test with empty video IDs list (should return results from all videos)
    empty_list_results = db.find_similar_chunks(query_embedding, video_ids=[])
    assert len(empty_list_results) >= 3  # Should get results from all videos
    
    # Test with non-existent video IDs
    nonexistent_results = db.find_similar_chunks(query_embedding, video_ids=['nonexistent'])
    assert len(nonexistent_results) == 0

def test_hybrid_search_chunks(temp_db, sample_video_data, sample_summary, sample_chunks):
    """Test hybrid search combining FTS and semantic vector search using RRF."""
    # Store the sample video data (creates FTS and semantic entries)
    db.store_video(sample_video_data, sample_summary, sample_chunks)
    
    # Use a query string that should match via FTS and an embedding similar to one of the stored chunks.
    query = "test"
    query_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    
    results = db.hybrid_search_chunks(query, query_embedding, limit=5)
    
    # Ensure that some results are returned
    assert results, "Hybrid search returned no results"
    
    # Verify that results are sorted in descending order by their combined RRF score.
    for i in range(len(results) - 1):
        assert results[i]["rrf_score"] >= results[i + 1]["rrf_score"], "Results are not sorted by RRF score"
    
    # Verify that key fields are present in results.
    for result in results:
        for key in ("chunk_id", "chunk_text", "rrf_score", "video_id"):
            assert key in result, f"Result missing key: {key}"
