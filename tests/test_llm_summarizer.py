"""
Tests for the LLM summarization functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
from pydantic import BaseModel
import json
from ytq.llm import (summarize_transcript,
    _summarize_with_openai,
    _summarize_with_anthropic,
    YTSummarize
)

@pytest.fixture
def sample_chunks():
    """Sample transcript chunks for testing."""
    return [
        {
            "text": "Hello and welcome to this video about Python programming. Today we'll cover basic concepts.",
            "timestamp": 0,
            "end_timestamp": 10,
            "entries": []
        },
        {
            "text": "First, let's talk about variables. Variables are used to store data in Python.",
            "timestamp": 11,
            "end_timestamp": 20,
            "entries": []
        },
        {
            "text": "Next, we'll discuss functions. Functions help us organize and reuse code.",
            "timestamp": 21,
            "end_timestamp": 30,
            "entries": []
        }
    ]

@pytest.fixture
def sample_metadata():
    """Sample video metadata for testing."""
    return {
        "title": "Python Programming Basics",
        "author": "Coding Teacher",
        "duration": 300,
        "video_id": "abc123",
        "url": "https://youtube.com/watch?v=abc123"
    }

@pytest.fixture
def valid_summary():
    """A valid summary structure for testing."""
    return {
        "tldr": "This video covers the fundamentals of Python programming including variables and functions.",
        "summary": """Introduction to Python programming basics. Variables are used to store data in Python.
            Functions help organize and reuse code""",
        "tags": ["python", "programming", "tutorial", "beginners"]
    }

import os
import pytest
from unittest.mock import patch, MagicMock
from ytq.llm import _summarize_with_openai, YTSummarize

@patch('openai.OpenAI')
def test__summarize_with_openai_success(mock_openai, valid_summary):
    # Ensure the API key is set for the test.
    with patch.dict(os.environ, {"OPENAI_API_KEY": "fake-key"}):
        # Create pydantic response obj
        class FakeResponse(BaseModel):
            tldr: str
            summary: str
            tags: list[str]

        fake_summary = FakeResponse(**valid_summary)
        # Create a fake message object with a 'parsed' attribute.
        fake_message = MagicMock()
        fake_message.parsed = fake_summary
        
        # Create a fake choice that holds our fake message.
        fake_choice = MagicMock()
        fake_choice.message = fake_message
        
        # Create a fake completion object with a choices list.
        fake_completion = MagicMock()
        fake_completion.choices = [fake_choice]
        
        # Create a fake parse function that returns our fake completion.
        fake_parse = MagicMock(return_value=fake_completion)
        
        # Construct a fake client with the nested attribute structure expected.
        fake_client = MagicMock()
        fake_client.beta.chat.completions.parse = fake_parse
        
        # Configure the openai client mock to return our fake client.
        mock_openai.return_value = fake_client
        
        prompt = "Test transcript prompt for summarization."
        result = _summarize_with_openai(prompt, YTSummarize, model="test-model")
        
        # Verify that the parse function was called with the expected parameters.
        fake_parse.assert_called_once_with(
            model="test-model",
            messages=[
                {"role": "system", "content": "You are an expert video summarizer."},
                {"role": "user", "content": prompt},
            ],
            response_format=YTSummarize
        )
        
        # Assert the result matches the fake summary's dict representation.
        assert result == fake_summary.model_dump()

def test__summarize_with_openai_api_key_missing():
    # Ensure the API key is not set.
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable not set"):
            _summarize_with_openai("Any prompt", YTSummarize)


@patch('anthropic.Anthropic')
def test__summarize_with_anthropic_success(mock_anthropic, valid_summary):
    # Ensure the API key is set for the test.
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake-key"}):

        fake_summary = json.dumps(valid_summary)
        # Create a fake choice that holds our fake message.
        fake_content = MagicMock()
        fake_content.text = fake_summary
        
        # Create a fake completion object with a choices list.
        fake_response = MagicMock()
        fake_response.content = [fake_content]
        
        # Create a fake parse function that returns our fake completion.
        fake_create = MagicMock(return_value=fake_response)
        
        # Construct a fake client with the nested attribute structure expected.
        fake_client = MagicMock()
        fake_client.messages.create = fake_create
        
        # Configure the anthropic client mock to return our fake client.
        mock_anthropic.return_value = fake_client
        
        prompt = "Test transcript prompt for summarization."
        result = _summarize_with_anthropic(prompt, YTSummarize, model="test-model")
        
        # Verify that the parse function was called with the expected parameters.
        fake_create.assert_called_once_with(
            model="test-model",
            system=f"Your are expert video summarizer. You must respond with JSON that conforms to this schema: {YTSummarize.model_json_schema()}. Do not include any explanations or text outside the JSON.",
            messages=[
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
        )
        
        # Assert the result matches the fake summary's dict representation.
        assert result == valid_summary

def test__summarize_with_anthropic_api_key_missing():
    # Ensure the API key is not set.
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY environment variable not set"):
            _summarize_with_anthropic("Any prompt", YTSummarize)


@patch('ytq.llm._summarize_with_openai')
def test_summarize_transcript_openai(mock_openai, sample_chunks, sample_metadata, valid_summary):
    # Configure the mock to return the sample summary.
    mock_openai.return_value = valid_summary
    
    result = summarize_transcript(
        chunks=sample_chunks,
        metadata=sample_metadata,
        summary_func=YTSummarize,
        provider="openai",
        model="test-model"
    )
    
    # Ensure _summarize_with_openai was called.
    mock_openai.assert_called_once()
    assert result == valid_summary

@patch('ytq.llm._summarize_with_anthropic')
def test_summarize_transcript_anthropic(mock_anthropic, sample_chunks, sample_metadata, valid_summary):
    # Configure the mock to return the sample summary.
    mock_anthropic.return_value = valid_summary
    
    result = summarize_transcript(
        chunks=sample_chunks,
        metadata=sample_metadata,
        summary_func=YTSummarize,
        provider="anthropic",
        model="test-model"
    )
    
    # Ensure _summarize_with_anthropic was called.
    mock_anthropic.assert_called_once()
    assert result == valid_summary