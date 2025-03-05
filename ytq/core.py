"""
Core functionality for transcript download, chunking, and LLM summarization.
"""
import yt_dlp
import re

def download_transcript(url: str) -> dict:
    """
    Download transcript from a YouTube video URL.
    
    Args:
        url: YouTube video URL
        
    Returns:
        Dictionary containing transcript text with timestamps
        
    Raises:
        ValueError: If no transcript is found or URL is invalid
    """
    # Validate URL format
    if not re.match(r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]{11}', url):
        raise ValueError(f"Invalid YouTube URL format: {url}")
    
    # Configure yt-dlp options
    ydl_opts = {
        'skip_download': True,  # Don't download the video
        'writesubtitles': True,  # Write subtitles
        'writeautomaticsub': True,  # Write auto-generated subtitles if available
        'subtitleslangs': ['en'],
        'quiet': True,  # Suppress output
    }
    
    try:
        # Extract info with yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # store metadata for the video
            metadata = {
                "title": info.get('title', 'Unknown Title'),
                "author": info.get('uploader', 'Unknown Author'),
                "channel_id": info.get('channel_id', 'Unknown Channel'),
                "duration": info.get('duration', 0),  # Duration in seconds
                "video_id": info.get('id', 'Unknown ID'),
                "url": url,
                "upload_date": info.get('upload_date', 'Unknown Date'),
                "view_count": info.get('view_count', 0),
                "description": info.get('description', ''),
                "categories": info.get('categories', []),
                "tags": info.get('tags', [])
            }
            # Check if subtitles are available
            if not info.get('subtitles') and not info.get('automatic_captions'):
                raise ValueError(f"No English transcript found for video: {url}")
            
            # Try to get manual subtitles first, fall back to automatic captions
            subtitles = info.get('subtitles', {}).get('en')
            if not subtitles:
                subtitles = info.get('automatic_captions', {}).get('en')
            
            if not subtitles:
                raise ValueError(f"No English transcript found for video: {url}")
            
            # Try to get the transcript in JSON format first
            transcript_url = None
            transcript_format = None
            
            # First try JSON format
            for fmt in subtitles:
                if fmt.get('ext') == 'json':
                    transcript_url = fmt.get('url')
                    transcript_format = 'json'
                    break
            
            # Fall back to VTT format if JSON is not available
            if not transcript_url:
                for fmt in subtitles:
                    if fmt.get('ext') == 'vtt':
                        transcript_url = fmt.get('url')
                        transcript_format = 'vtt'
                        break
            
            if not transcript_url:
                raise ValueError(f"No suitable transcript format available for video: {url}")
            
            # Download the transcript
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                transcript_data = ydl.urlopen(transcript_url).read().decode('utf-8')
            
            # Parse the transcript data based on format
            transcript_entries = []
            
            if transcript_format == 'json':
                import json
                transcript_entries = json.loads(transcript_data)
            elif transcript_format == 'vtt':
                transcript_entries = parse_vtt_transcript(transcript_data)
            
            # Extract text and timestamps
            transcript_text = ""
            timestamps = []
            
            for entry in transcript_entries:
                start = entry.get('start', 0)
                text = entry.get('text', '')
                
                transcript_text += text + " "
                timestamps.append(start)
            
            return {
                "transcript": transcript_text.strip(),
                "timestamps": timestamps,
                "entries": transcript_entries,  # Include the full entries for more detailed processing
                "metadata": metadata
            }
                
    except yt_dlp.utils.DownloadError as e:
        raise ValueError(f"Error downloading transcript: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unexpected error processing transcript: {str(e)}")

def parse_vtt_transcript(vtt_data: str) -> list:
    """
    Parse VTT format transcript data into a list of entries with start times and text.
    
    Args:
        vtt_data: Raw VTT format transcript data
        
    Returns:
        List of dictionaries with 'start' and 'text' keys
    """
    import re
    
    # Regular expression to match timestamp and text in VTT format
    # Format example: 00:00:00.000 --> 00:00:05.000
    # Text follows on the next line(s) until a blank line
    timestamp_pattern = re.compile(r'(\d+:\d+:\d+\.\d+) --> (\d+:\d+:\d+\.\d+)')
    html_tag_pattern = re.compile(r'<[^>]+>')
    
    entries = []
    current_start = None
    current_text = []
    
    lines = vtt_data.strip().split('\n')
    
    # Skip the header (first line is "WEBVTT" and possibly some metadata lines)
    start_idx = 0
    for i, line in enumerate(lines):
        if line.strip() == "":
            start_idx = i + 1
            break
    
    i = start_idx
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines, numeric identifiers and lines with HTML tags
        if not line or line.isdigit() or html_tag_pattern.search(line):
            i += 1
            continue
        
        # Check for timestamp
        match = timestamp_pattern.match(line)
        if match:
            # If we already have a timestamp and text, save the entry
            if current_start is not None and current_text:
                entries.append({
                    'start': current_start,
                    'text': ' '.join(current_text).strip()
                })
                current_text = []
                current_start = None
            
            # Parse the start timestamp (convert to seconds)
            if not current_start:
                start_str = match.group(1)
                h, m, s = start_str.split(':')
                current_start = float(h) * 3600 + float(m) * 60 + float(s)
            
            i += 1
        elif current_start is not None:
            # This is text content
            if line:
                if entries and entries[-1]['text'] == line.strip():
                    # If the last entry is the same as the current text, skip adding it
                    pass
                else:
                    current_text.append(line.replace('&nbsp;', ''))
            i += 1
        else:
            # Skip lines until we find a timestamp
            i += 1
    
    # Add the last entry if there is one
    if current_start is not None and current_text:
        entries.append({
            'start': current_start,
            'text': ' '.join(current_text).strip()
        })
    # Deduplicate entries based on text (works dicts cannot have duplicate keys, preserve order)
    entries_unique = list({d['text']: d for d in entries if d['text'] not in {prev['text'] for prev in entries[:entries.index(d)]}}.values())
    return entries_unique


def chunk_transcript(transcript_data: dict, chunk_size: int = 1000, chunk_overlap: int = 100) -> list:
    """
    Split transcript into manageable chunks while preserving timestamps.
    
    Args:
        transcript_data: Dictionary containing transcript text with timestamps and entries
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks
        
    Returns:
        List of chunks, each with text, timestamp, and end_timestamp
    """
    if not transcript_data or 'entries' not in transcript_data or not transcript_data['entries']:
        raise ValueError("Invalid transcript data: missing entries")
    
    entries = transcript_data['entries']
    chunks = []
    
    # Process by combining entries until we reach the chunk size
    current_chunk_text = ""
    current_chunk_entries = []
    
    for entry in entries:
        entry_text = entry.get('text', '')
        
        # Skip empty entries
        if not entry_text.strip():
            continue
            
        # If adding this entry would exceed chunk size and we already have content,
        # finalize the current chunk and start a new one
        if len(current_chunk_text) + len(entry_text) > chunk_size and current_chunk_entries:
            # Create chunk with the collected entries
            start_timestamp = current_chunk_entries[0].get('start', 0)
            end_timestamp = current_chunk_entries[-1].get('start', 0)
            
            chunks.append({
                "text": current_chunk_text.strip(),
                "timestamp": start_timestamp,
                "end_timestamp": end_timestamp,
                "entries": current_chunk_entries
            })
            
            # Start a new chunk with overlap
            # Find entries to include in the overlap
            overlap_text = ""
            overlap_entries = []
            
            # Work backwards through current entries to create overlap
            for i in range(len(current_chunk_entries) - 1, -1, -1):
                entry_to_check = current_chunk_entries[i]
                entry_text_to_check = entry_to_check.get('text', '')
                
                if len(overlap_text) + len(entry_text_to_check) <= chunk_overlap:
                    overlap_text = entry_text_to_check + " " + overlap_text
                    overlap_entries.insert(0, entry_to_check)
                else:
                    break
            
            # Initialize new chunk with overlap content
            current_chunk_text = overlap_text
            current_chunk_entries = overlap_entries.copy()
        
        # Add the current entry to the chunk
        current_chunk_text += entry_text + " "
        current_chunk_entries.append(entry)
    
    # Add the final chunk if there's any content left
    if current_chunk_entries:
        start_timestamp = current_chunk_entries[0].get('start', 0)
        end_timestamp = current_chunk_entries[-1].get('start', 0)
        
        chunks.append({
            "text": current_chunk_text.strip(),
            "timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "entries": current_chunk_entries
        })
    
    return chunks

def chunk_by_sentences(transcript_data: dict, max_sentences: int = 5, overlap_sentences: int = 1) -> list:
    """
    Split transcript into chunks by sentences while preserving timestamps.
    
    Args:
        transcript_data: Dictionary containing transcript text with timestamps and entries
        max_sentences: Maximum number of sentences per chunk
        overlap_sentences: Number of sentences to overlap between chunks
        
    Returns:
        List of chunks, each with text, timestamp, and end_timestamp
    """
    if not transcript_data or 'entries' not in transcript_data or not transcript_data['entries']:
        raise ValueError("Invalid transcript data: missing entries")
    
    import re
    
    # Combine all entries into a single text with timestamp mapping
    full_text = ""
    timestamp_map = []
    
    for entry in transcript_data['entries']:
        start_pos = len(full_text)
        entry_text = entry.get('text', '')
        full_text += entry_text + " "
        end_pos = len(full_text) - 1
        
        timestamp_map.append({
            'start_pos': start_pos,
            'end_pos': end_pos,
            'timestamp': entry.get('start', 0)
        })
    
    # Split text into sentences
    # This is a simple sentence splitter - for production, consider using nltk or spacy
    sentence_pattern = re.compile(r'[.!?]+\s+')
    sentence_ends = [m.end() for m in sentence_pattern.finditer(full_text)]
    
    # Add the end of text as the last sentence end if it's not already included
    if not sentence_ends or sentence_ends[-1] < len(full_text):
        sentence_ends.append(len(full_text))
    
    # Create chunks of sentences
    chunks = []
    i = 0
    
    while i < len(sentence_ends):
        # Determine chunk boundaries
        chunk_start = 0 if i == 0 else sentence_ends[i - overlap_sentences]
        chunk_end = sentence_ends[min(i + max_sentences - 1, len(sentence_ends) - 1)]
        
        # Extract chunk text
        chunk_text = full_text[chunk_start:chunk_end].strip()
        
        # Find timestamps for this chunk
        start_timestamp = None
        end_timestamp = None
        chunk_entries = []
        
        for entry_map in timestamp_map:
            # If entry overlaps with chunk, include it
            if (entry_map['start_pos'] <= chunk_end and entry_map['end_pos'] >= chunk_start):
                if start_timestamp is None or entry_map['timestamp'] < start_timestamp:
                    start_timestamp = entry_map['timestamp']
                
                if end_timestamp is None or entry_map['timestamp'] > end_timestamp:
                    end_timestamp = entry_map['timestamp']
                
                # Find the original entry
                for entry in transcript_data['entries']:
                    if entry.get('start') == entry_map['timestamp']:
                        if entry not in chunk_entries:
                            chunk_entries.append(entry)
        
        # Create the chunk
        chunks.append({
            "text": chunk_text,
            "timestamp": start_timestamp or 0,
            "end_timestamp": end_timestamp or 0,
            "entries": chunk_entries
        })
        
        # Move to next set of sentences with overlap
        i += max_sentences - overlap_sentences
    
    return chunks

