"""
Database operations for storing and retrieving video data.
"""
import sqlite3
import struct
import json
import pathlib

# functions to encode/decode embeddings into a little-endian binary sequences of 32-bit floating point numbers,
# each represented using 4 bytes. Store those as BLOB columns in the database.
def encode(values):
    return struct.pack("<" + "f" * len(values), *values)

def decode(binary):
    return struct.unpack("<" + "f" * (len(binary) // 4), binary)


def get_db_path() -> pathlib.Path:
    """
    Get the path to the SQLite database file.
    
    Returns:
        Path to the database file
    """
    # Create ~/.ytq directory if it doesn't exist
    db_dir = pathlib.Path.home() / ".ytq"
    db_dir.mkdir(exist_ok=True)
    return db_dir / "ytq.db"

def init_db() -> None:
    """
    Initialize the database with the required schema.
    """
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Create videos table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS videos (
        video_id TEXT PRIMARY KEY,
        url TEXT NOT NULL,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        duration INTEGER NOT NULL,
        view_count INTEGER,
        upload_date TEXT NOT NULL,
        video_description TEXT,
        summary TEXT NOT NULL,
        tldr TEXT,
        tags TEXT,
        full_transcript TEXT,
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create video_details table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS video_details (
        chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id TEXT NOT NULL,
        chunk_text TEXT NOT NULL,
        embedding BLOB,
        timestamp REAL NOT NULL,
        end_timestamp REAL NOT NULL,
        entries TEXT,
        FOREIGN KEY (video_id) REFERENCES videos (video_id)
    )
    ''')
    
    # Create an index on video_id in video_details for faster lookups
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_video_details_video_id 
    ON video_details(video_id)
    ''')
    
    # Create virtual FTS5 table for videos
    cursor.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS videos_fts USING fts5(
        video_id,
        title,
        video_description,
        summary,
        tldr,
        tags,
        full_transcript
    )
    ''')
    
    # Create triggers to keep videos_fts in sync with videos
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS videos_ai AFTER INSERT ON videos BEGIN
        INSERT INTO videos_fts(video_id, title, video_description, summary, tldr, tags, full_transcript)
        VALUES (new.video_id, new.title, new.video_description, new.summary, new.tldr, new.tags, new.full_transcript);
    END;
    ''')
    
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS videos_ad AFTER DELETE ON videos BEGIN
        DELETE FROM videos_fts WHERE video_id = old.video_id;
    END;
    ''')
    
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS videos_au AFTER UPDATE ON videos BEGIN
        DELETE FROM videos_fts WHERE video_id = old.video_id;
        INSERT INTO videos_fts(video_id, title, video_description, summary, tldr, tags, full_transcript)
        VALUES (new.video_id, new.title, new.video_description, new.summary, new.tldr, new.tags, new.full_transcript);
    END;
    ''')
    
    # Create virtual FTS5 table for video_details
    cursor.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS video_details_fts USING fts5(
        chunk_id,
        chunk_text,
        content='video_details'
    )
    ''')
    
    # Create triggers to keep video_details_fts in sync with video_details
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS video_details_ai AFTER INSERT ON video_details BEGIN
        INSERT INTO video_details_fts(rowid, chunk_text)
        VALUES (new.chunk_id, new.chunk_text);
    END;
    ''')
    
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS video_details_ad AFTER DELETE ON video_details BEGIN
        -- DELETE FROM video_details_fts WHERE chunk_id = old.chunk_id;
        INSERT INTO video_details_fts(video_details_fts, rowid, chunk_text)
        VALUES ('delete', old.chunk_id, old.chunk_text);
    END;
    ''')
    
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS video_details_au AFTER UPDATE ON video_details BEGIN
        -- DELETE FROM video_details_fts WHERE chunk_id = old.chunk_id;
        INSERT INTO video_details_fts(video_details_fts, rowid, chunk_text)
        VALUES ('delete', old.chunk_id, old.chunk_text);
        INSERT INTO video_details_fts(rowid, chunk_text)
        VALUES (new.chunk_id, new.chunk_text);
    END;
    ''')
    
    conn.commit()
    conn.close()

def dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict[str, any]:
    """
    Convert SQL row to dictionary for easier handling.
    
    Args:
        cursor: SQLite cursor
        row: Row tuple from SQLite
        
    Returns:
        Dictionary representing the row
    """
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def store_video(video_data: dict[str, any], summary: dict[str, any], chunks: list[dict[str, any]]) -> None:
    """
    Store video data, summary, and chunks in the database.
    If the video already exists, it will be updated.
    
    Args:
        video_data: Video containing metadata and full transcript. Dictionary with keys metadata and transcript.
        summary: Structured summary, tags and tldr (output from LLM summarization). Dictionary with keys summary, tldr, tags.
        chunks: List of transcript chunks with embeddings (output from embedding generation). 
    """
    # Extract metadata from video_data
    metadata = video_data.get('metadata')
    full_transcript = video_data.get('transcript')
    video_id = metadata.get('video_id')
    if not video_id:
        raise ValueError("Missing video_id in video_data")
        
    # Prepare video data for insertion/update
    tags = summary.get('tags')
    tags_json = json.dumps(tags) if tags else None
    
    video_values = (
        video_id,
        metadata.get('url', ''),
        metadata.get('title', 'Unknown Title'),
        metadata.get('author', 'Unknown Author'),
        metadata.get('duration', 0),
        metadata.get('view_count', 0),
        metadata.get('upload_date', ''),
        metadata.get('description', ''),
        summary.get('summary'),
        summary.get('tldr'),
        tags_json,
        full_transcript
    )
    
    # Use context manager to ensure connection is properly closed
    with sqlite3.connect(get_db_path()) as conn:
        cursor = conn.cursor()
        
        # Check if video already exists
        cursor.execute("SELECT video_id FROM videos WHERE video_id = ?", (video_id,))
        existing = cursor.fetchone()
        
        try:
            if existing:
                # Delete existing chunks to avoid duplicates
                cursor.execute("DELETE FROM video_details WHERE video_id = ?", (video_id,))
                # Delete the video
                cursor.execute("DELETE FROM videos WHERE video_id = ?", (video_id,))
                # Insert the updated video
                cursor.execute('''
                INSERT INTO videos 
                (video_id, url, title, author, duration, view_count, upload_date, 
                 video_description, summary, tldr, tags, full_transcript)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', video_values)
                # Rebuild FTS table
                # cursor.execute("INSERT INTO videos_fts(videos_fts) VALUES('rebuild')")
                # cursor.execute("INSERT INTO video_details_fts(video_details_fts) VALUES('rebuild')")
            else:
                # Insert new video
                cursor.execute('''
                INSERT INTO videos 
                (video_id, url, title, author, duration, view_count, upload_date, 
                 video_description, summary, tldr, tags, full_transcript)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', video_values)
            
            # Insert chunks with embeddings
            for chunk in chunks:
                # Encode the embedding if available
                embedding_blob = None
                if 'embedding' in chunk and chunk['embedding']:
                    embedding_blob = encode(chunk['embedding'])
                
                # Store entries as JSON
                entries_json = json.dumps(chunk.get('entries', [])) if chunk.get('entries') else None
                
                cursor.execute('''
                INSERT INTO video_details 
                (video_id, chunk_text, embedding, timestamp, end_timestamp, entries)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    video_id,
                    chunk.get('text', ''),
                    embedding_blob,
                    chunk.get('timestamp', 0),
                    chunk.get('end_timestamp', 0),
                    entries_json
                ))
            
            # Commit is automatic with context manager when no exception occurs
        except Exception as e:
            # Rollback is automatic with context manager when exception occurs
            raise e

def get_video(video_id: str) -> dict[str, any]|None:
    """
    Retrieve a video by its ID.
    
    Args:
        video_id: ID of the video to retrieve
        
    Returns:
        Dictionary containing video data or None if not found
    """
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = dict_factory
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT * FROM videos WHERE video_id = ?
        ''', (video_id,))
        
        video = cursor.fetchone()
        
        if video:
            # Parse JSON fields
            if video.get('tags'):
                video['tags'] = json.loads(video['tags'])
            
            # Get associated chunks
            cursor.execute('''
            SELECT chunk_id, chunk_text, timestamp, end_timestamp, entries FROM video_details 
            WHERE video_id = ? ORDER BY timestamp
            ''', (video_id,))
            
            chunks = cursor.fetchall()
            for chunk in chunks:
                if chunk.get('entries'):
                    chunk['entries'] = json.loads(chunk['entries'])
            
            video['chunks'] = chunks
            
        return video
    finally:
        conn.close()

def get_video_chunks(video_id: str, with_embeddings: bool = False) -> list[dict[str, any]]:
    """
    Retrieve all chunks for a specific video.
    
    Args:
        video_id: ID of the video
        with_embeddings: Whether to include embeddings in the result
        
    Returns:
        List of chunk dictionaries
    """
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = dict_factory
    
    try:
        cursor = conn.cursor()
        
        if with_embeddings:
            cursor.execute('''
            SELECT chunk_id, chunk_text, embedding, timestamp, end_timestamp, entries FROM video_details 
            WHERE video_id = ? ORDER BY timestamp
            ''', (video_id,))
        else:
            cursor.execute('''
            SELECT chunk_id, chunk_text, timestamp, end_timestamp, entries FROM video_details 
            WHERE video_id = ? ORDER BY timestamp
            ''', (video_id,))
        
        chunks = cursor.fetchall()
        
        # Process embeddings and entries
        for chunk in chunks:
            if with_embeddings and chunk.get('embedding'):
                chunk['embedding'] = list(decode(chunk['embedding']))
            
            if chunk.get('entries'):
                chunk['entries'] = json.loads(chunk['entries'])
        
        return chunks
    finally:
        conn.close()

def search_videos(query: str, limit: int = 10) -> list[dict[str, any]]:
    """
    Search for videos using full-text search.
    
    Args:
        query: Search query
        limit: Maximum number of results to return
        
    Returns:
        List of matching videos
    """
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = dict_factory
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT videos.* FROM videos_fts 
        JOIN videos ON videos_fts.video_id = videos.video_id
        WHERE videos_fts MATCH ? 
        ORDER BY rank
        LIMIT ?
        ''', (query, limit))
        
        videos = cursor.fetchall()
        
        # Parse JSON fields
        for video in videos:
            if video.get('tags'):
                video['tags'] = json.loads(video['tags'])
        
        return videos
    finally:
        conn.close()

def search_chunks(query: str, limit: int = 20) -> list[dict[str, any]]:
    """
    Search for video chunks using full-text search.
    
    Args:
        query: Search query
        limit: Maximum number of results to return
        
    Returns:
        List of matching chunks with video metadata
    """
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = dict_factory
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT vd.chunk_id, vd.video_id, vd.chunk_text, vd.timestamp, vd.end_timestamp,
               v.title, v.author, v.url
        FROM video_details_fts 
        JOIN video_details vd ON video_details_fts.chunk_id = vd.chunk_id
        JOIN videos v ON vd.video_id = v.video_id
        WHERE video_details_fts MATCH ? 
        ORDER BY rank
        LIMIT ?
        ''', (query, limit))
        
        return cursor.fetchall()
    finally:
        conn.close()

def get_all_videos(limit: int = 100, offset: int = 0) -> list[dict[str, any]]:
    """
    Retrieve all videos with pagination.
    
    Args:
        limit: Maximum number of videos to return
        offset: Number of videos to skip
        
    Returns:
        List of video dictionaries
    """
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = dict_factory
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT video_id, title, author, duration, view_count, upload_date, summary, tldr, tags, processed_at 
        FROM videos 
        ORDER BY processed_at DESC
        LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        videos = cursor.fetchall()
        
        # Parse JSON fields
        for video in videos:
            if video.get('tags'):
                video['tags'] = json.loads(video['tags'])
        
        return videos
    finally:
        conn.close()

def delete_video(video_id: str) -> bool:
    """
    Delete a video and its associated chunks.
    
    Args:
        video_id: ID of the video to delete
        
    Returns:
        True if successful, False otherwise
    """
    conn = sqlite3.connect(get_db_path())
    
    try:
        cursor = conn.cursor()
        
        # Delete chunks first (due to foreign key constraint)
        cursor.execute("DELETE FROM video_details WHERE video_id = ?", (video_id,))
        
        # Delete the video
        cursor.execute("DELETE FROM videos WHERE video_id = ?", (video_id,))
        
        affected_rows = cursor.rowcount
        conn.commit()
        
        return affected_rows > 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def find_similar_chunks(embedding: list[float], limit: int = 5, video_ids: list[str] = None) -> list[dict[str, any]]:
    """
    Find chunks with similar embeddings using cosine similarity.
    
    Args:
        embedding: Query embedding vector as a list of floats
        limit: Maximum number of results to return
        video_ids: Optional list of video IDs to restrict search to specific videos
        
    Returns:
        List of chunks with similarity scores, sorted by relevance
    """
    import numpy as np
    
    def fast_dot_product(query: np.ndarray, matrix: np.ndarray, k=3) -> tuple[np.ndarray, np.ndarray]:
        dot_products = query @ matrix.T
        idx = np.argpartition(dot_products, -k)[-k:]
        idx = idx[np.argsort(dot_products[idx])[::-1]]
        score = dot_products[idx]
        return idx, score

    conn = sqlite3.connect(get_db_path())
    conn.row_factory = dict_factory
    
    try:
        cursor = conn.cursor()
        
        # Convert query embedding to numpy array
        query_embedding = np.array(embedding, dtype=np.float32)
        
        # Get chunks with embeddings, optionally filtered by video_ids
        if video_ids and len(video_ids) > 0:
            # Create placeholders for SQL IN clause
            placeholders = ', '.join(['?'] * len(video_ids))
            cursor.execute(f'''
            SELECT vd.chunk_id, vd.video_id, vd.chunk_text, vd.embedding, vd.timestamp, vd.end_timestamp,
                   v.title, v.author, v.url
            FROM video_details vd
            JOIN videos v ON vd.video_id = v.video_id
            WHERE vd.embedding IS NOT NULL AND vd.video_id IN ({placeholders})
            ''', video_ids)
        else:
            cursor.execute('''
            SELECT vd.chunk_id, vd.video_id, vd.chunk_text, vd.embedding, vd.timestamp, vd.end_timestamp,
                   v.title, v.author, v.url
            FROM video_details vd
            JOIN videos v ON vd.video_id = v.video_id
            WHERE vd.embedding IS NOT NULL
            ''')
        
        chunks = cursor.fetchall()
        
        # Early return if no chunks with embeddings are found
        if not chunks:
            return []
            
        # Extract embeddings and build a matrix
        chunk_ids = []
        metadata = []
        embeddings_matrix = np.zeros((len(chunks), len(embedding)), dtype=np.float32)
        
        for i, chunk in enumerate(chunks):
            if chunk['embedding']:
                # Decode the embedding from binary to float list
                chunk_vector = decode(chunk['embedding'])
                embeddings_matrix[i] = chunk_vector
                chunk_ids.append(chunk['chunk_id'])
                metadata.append({
                    'chunk_id': chunk['chunk_id'],
                    'video_id': chunk['video_id'],
                    'title': chunk['title'],
                    'author': chunk['author'],
                    'chunk_text': chunk['chunk_text'],
                    'timestamp': chunk['timestamp'],
                    'end_timestamp': chunk['end_timestamp'],
                    'url': chunk.get('url', '')
                })
        
        # Use fast_dot_product for efficient similarity calculation
        indices, scores = fast_dot_product(query_embedding, embeddings_matrix, k=min(limit, len(chunks)))
        
        # Create results with similarity scores
        results = []
        for idx, score in zip(indices, scores):
            result = metadata[idx].copy()
            result['similarity'] = float(score)  # Convert numpy float to Python float
            results.append(result)
        
        return results
    finally:
        conn.close()

def hybrid_search_chunks(query: str, embedding: list[float], limit: int = 10, video_ids: list[str] = None, k: int = 60) -> list[dict[str, any]]:
    """
    Perform a hybrid search using Reciprocal Rank Fusion (RRF) that combines
    full-text search (FTS) results with semantic vector search results.
    
    Args:
        query: Full-text search query.
        embedding: Query embedding vector.
        limit: Maximum number of results to return.
        video_ids: Optional list of video IDs to restrict semantic search.
        k: RRF constant to dampen the reciprocal rank (default: 60).
    
    Returns:
        List of result dictionaries with a combined "rrf_score", sorted by relevance.
    """
    # Retrieve results from full-text search (FTS)
    fts_results = search_chunks(query, limit=limit * 2)
    # Retrieve results from semantic vector search
    semantic_results = find_similar_chunks(embedding, limit=limit * 2, video_ids=video_ids)
    
    # Use Reciprocal Rank Fusion to combine scores.
    combined = {}
    
    # Process FTS results; rank starts at 1 for highest result.
    for rank, result in enumerate(fts_results, start=1):
        chunk_id = result["chunk_id"]
        score = 1.0 / (k + rank)
        if chunk_id in combined:
            combined[chunk_id]["rrf_score"] += score
        else:
            temp = result.copy()
            temp["rrf_score"] = score
            combined[chunk_id] = temp
    
    # Process semantic results.
    for rank, result in enumerate(semantic_results, start=1):
        chunk_id = result["chunk_id"]
        score = 1.0 / (k + rank)
        if chunk_id in combined:
            combined[chunk_id]["rrf_score"] += score
        else:
            temp = result.copy()
            temp["rrf_score"] = score
            combined[chunk_id] = temp
    
    # Sort the merged results by their combined RRF score in descending order.
    merged_results = list(combined.values())
    merged_results.sort(key=lambda x: x["rrf_score"], reverse=True)
    
    return merged_results[:limit]
