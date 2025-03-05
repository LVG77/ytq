"""
Tests for the transcript download functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
from ytq.core import download_transcript, parse_vtt_transcript

@pytest.mark.parametrize("url", [
    "not-a-url",
    "http://example.com",
    "youtube.com/channel/123",
    "https://youtube.com/playlist?list=123"
])
def test_invalid_url_format(url):
    """Test that invalid URL formats raise ValueError."""
    # for url in invalid_urls:
    with pytest.raises(ValueError, match="Invalid YouTube URL format"):
        download_transcript(url)

@patch('yt_dlp.YoutubeDL')
def test_no_transcript_available(mock_ydl):
    """Test that videos without transcripts raise ValueError."""
    # Configure the mock to return info without subtitles
    mock_instance = MagicMock()
    mock_ydl.return_value.__enter__.return_value = mock_instance
    mock_instance.extract_info.return_value = {
        'id': 'sample_id',
        'title': 'Sample Video',
        'subtitles': {},
        'automatic_captions': {}
    }
    
    with pytest.raises(ValueError, match="No English transcript found"):
        download_transcript("https://youtube.com/watch?v=sample_id00")

@patch('yt_dlp.YoutubeDL')
def test_successful_transcript_download(mock_ydl):
    """Test successful transcript download."""
    # Configure the mock to return sample transcript data
    mock_instance = MagicMock()
    mock_ydl.return_value.__enter__.return_value = mock_instance
    
    # Mock extract_info to return video info with subtitles
    mock_instance.extract_info.return_value = {
        'id': 'sample_id',
        'title': 'Sample Video',
        'subtitles': {
            'en': [
                {'ext': 'json', 'url': 'https://example.com/transcript.json'}
            ]
        }
    }
    
    # Mock urlopen to return sample transcript JSON
    mock_urlopen = MagicMock()
    mock_ydl.return_value.__enter__.return_value.urlopen.return_value = mock_urlopen
    mock_urlopen.read.return_value = b'''[
        {"start": 0.0, "duration": 2.0, "text": "Hello"},
        {"start": 2.0, "duration": 3.0, "text": "world"},
        {"start": 5.0, "duration": 4.0, "text": "this is a test"}
    ]'''
    
    # Call the function
    result = download_transcript("https://youtube.com/watch?v=sample_id00")
    
    # Verify the result
    assert "transcript" in result
    assert "timestamps" in result
    assert "entries" in result
    assert result["transcript"] == "Hello world this is a test"
    assert result["timestamps"] == [0.0, 2.0, 5.0]
    assert len(result["entries"]) == 3

@patch('yt_dlp.YoutubeDL')
def test_automatic_captions_fallback(mock_ydl):
    """Test fallback to automatic captions when manual subtitles aren't available."""
    # Configure the mock to return info with only automatic captions
    mock_instance = MagicMock()
    mock_ydl.return_value.__enter__.return_value = mock_instance
    
    # Mock extract_info to return video info with automatic captions only
    mock_instance.extract_info.return_value = {
        'id': 'sample_id',
        'title': 'Sample Video',
        'subtitles': {},
        'automatic_captions': {
            'en': [
                {'ext': 'json', 'url': 'https://example.com/auto_transcript.json'}
            ]
        }
    }
    
    # Mock urlopen to return sample transcript JSON
    mock_urlopen = MagicMock()
    mock_ydl.return_value.__enter__.return_value.urlopen.return_value = mock_urlopen
    mock_urlopen.read.return_value = b'''[
        {"start": 0.0, "duration": 2.0, "text": "Auto-generated"},
        {"start": 2.0, "duration": 3.0, "text": "transcript"},
        {"start": 5.0, "duration": 4.0, "text": "example"}
    ]'''
    
    # Call the function
    result = download_transcript("https://youtube.com/watch?v=sample_id00")
    
    # Verify the result
    assert "transcript" in result
    assert result["transcript"] == "Auto-generated transcript example"
    assert result["timestamps"] == [0.0, 2.0, 5.0]

@patch('yt_dlp.YoutubeDL')
def test_vtt_format_fallback(mock_ydl):
    """Test fallback to VTT format when JSON format isn't available."""
    # Configure the mock to return info with only VTT format subtitles
    mock_instance = MagicMock()
    mock_ydl.return_value.__enter__.return_value = mock_instance
    
    # Mock extract_info to return video info with VTT format only
    mock_instance.extract_info.return_value = {
        'id': 'sample_id',
        'title': 'Sample Video',
        'subtitles': {
            'en': [
                {'ext': 'vtt', 'url': 'https://example.com/transcript.vtt'}
            ]
        }
    }
    
    # Mock urlopen to return sample VTT transcript
    mock_urlopen = MagicMock()
    mock_ydl.return_value.__enter__.return_value.urlopen.return_value = mock_urlopen
    mock_urlopen.read.return_value = b'''WEBVTT

1
00:00:00.000 --> 00:00:02.000
Hello

2
00:00:02.000 --> 00:00:05.000
world

3
00:00:05.000 --> 00:00:09.000
this is a test'''
    
    # Call the function
    result = download_transcript("https://youtube.com/watch?v=sample_id00")
    
    # Verify the result
    assert "transcript" in result
    assert result["transcript"] == "Hello world this is a test"
    assert result["timestamps"] == [0.0, 2.0, 5.0]

def test_parse_vtt_transcript():
    """Test the VTT transcript parsing function."""
    vtt_data = """
    WEBVTT
    Kind: captions
    Language: en

    1
    00:00:00.510 --> 00:00:02.500 align:start position:0%

    First<00:00:02.159><c> line</c><00:00:02.280><c>

    00:00:02.500 --> 00:00:02.510
    First line

    00:00:02.510 --> 00:00:05.090 align:start position:0%
    First line
    Second<00:00:04.000><c> line</c><00:00:04.160><c> with</c><00:00:04.680><c> continuation</c>

    00:00:05.090 --> 00:00:05.100
    Second line with continuation

    00:00:05.100 --> 00:01:09.290
    Second line with continuation
    Third<00:00:04.000><c> line</c><00:00:04.160><c> some</c><00:00:04.680><c> text</c>

    00:01:09.290 --> 00:01:09.300
    Third line some text
    """
    
    entries = parse_vtt_transcript(vtt_data)
    
    assert len(entries) == 3
    assert entries[0]['start'] == 0.51
    assert entries[0]['text'] == "First line"
    assert entries[1]['start'] == 2.51
    assert entries[1]['text'] == "Second line with continuation"
    assert entries[2]['start'] == 5.10
    assert entries[2]['text'] == "Third line some text"


def test_parse_vtt_transcript2():
    """Test the VTT transcript parsing function with a different VTT format."""
    vtt_data = """
    WEBVTT
    Kind: captions
    Language: en

    00:00:00.780 --> 00:00:05.940
    Hi everybody and welcome to Lesson 17&nbsp;
    of Practical Deep Learning for Coders.&nbsp;

    00:00:07.260 --> 00:00:12.720
    I'm really excited about what we're going&nbsp;
    to look at over the next lesson or two.&nbsp;

    00:00:13.380 --> 00:00:16.440
    It's actually been turning out really&nbsp;
    well, much better than I could have hoped.&nbsp;

    00:00:16.440 --> 00:00:19.680
    So I can't wait to dive in.
    Before I do, I'm just going&nbsp;&nbsp;
    """
    
    entries = parse_vtt_transcript(vtt_data)
    
    assert len(entries) == 4
    assert entries[0]['start'] == 0.78
    assert entries[0]['text'] == "Hi everybody and welcome to Lesson 17 of Practical Deep Learning for Coders."
    assert entries[1]['start'] == 7.26
    assert entries[1]['text'] == "I'm really excited about what we're going to look at over the next lesson or two."
    assert entries[2]['start'] == 13.38
    assert entries[2]['text'] == "It's actually been turning out really well, much better than I could have hoped."
    assert entries[3]['start'] == 16.44
    assert entries[3]['text'] == "So I can't wait to dive in. Before I do, I'm just going"
