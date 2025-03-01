"""
Core functionality for transcript download, chunking, and LLM summarization.
"""
import yt_dlp
import re
from typing import Any

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
                "entries": transcript_entries  # Include the full entries for more detailed processing
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
                    current_text.append(line)
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

def extract_metadata(url: str) -> dict:
    """
    Extract metadata from a YouTube video.
    
    Args:
        url: YouTube video URL
        
    Returns:
        Dictionary containing video metadata (title, author, duration, etc.)
    """
    # TODO: Implement metadata extraction using yt-dlp
    return {
        "title": "Sample Video",
        "author": "Sample Author",
        "duration": 600,
        "video_id": "sample_id",
        "url": url
    }

def chunk_transcript(transcript_data: dict) -> list:
    """
    Split transcript into manageable chunks while preserving timestamps.
    
    Args:
        transcript_data: Dictionary containing transcript text with timestamps
        
    Returns:
        List of chunks, each with text and timestamp
    """
    # TODO: Implement transcript chunking logic
    return [
        {"text": "Sample chunk 1", "timestamp": 0},
        {"text": "Sample chunk 2", "timestamp": 10}
    ]

def summarize_transcript(chunks: list, metadata: dict) -> dict:
    """
    Generate a summary of the transcript using an LLM.
    
    Args:
        chunks: List of transcript chunks
        metadata: Video metadata
        
    Returns:
        Structured JSON summary
    """
    # TODO: Implement LLM summarization
    return {
        "title": metadata["title"],
        "tldr": "Sample TLDR summary",
        "detailed_summary": [
            {"bullet": "Sample point 1", "timestamp": 0},
            {"bullet": "Sample point 2", "timestamp": 10}
        ],
        "tags": ["sample", "tags"]
    }

def generate_embeddings(summary_bullets: list) -> dict:
    """
    Generate embeddings for summary bullets.
    
    Args:
        summary_bullets: List of summary bullets
        
    Returns:
        Dictionary mapping bullets to embeddings
    """
    # TODO: Implement embedding generation
    return {
        "Sample point 1": [0.1, 0.2, 0.3],
        "Sample point 2": [0.4, 0.5, 0.6]
    }
