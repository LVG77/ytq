from pydantic import BaseModel

class YTSummarize(BaseModel):
    """
    Summarize a transcript of YouTube video that discusses some technical topic or tool.

    Write a clear summary of video's content. Add 2-3 sentence tldr section of the content.
    Add tags which are relevant keywords that describe the video content. Always include mentioned python libraries and modules in the tags.
    """
    tldr: str
    summary: str
    tags: list[str]

def summarize_transcript(chunks: list, metadata: dict, summary_func: BaseModel, provider: str = "openai", model: str = None) -> dict:
    """
    Generate a summary of the transcript using an LLM.
    
    Args:
        chunks: List of transcript chunks
        metadata: Video metadata
        summmary_func: Pydantic model for the summary
        provider: LLM provider to use ('openai' or 'anthropic')
        model: Specific model to use (if None, uses default for provider)
        
    Returns:
        Structured JSON summary
        
    Raises:
        ValueError: If the LLM response is invalid or provider is not supported
        RuntimeError: If there's an API error or timeout
    """
    # Combine chunks into a single text for processing
    full_transcript = "\n\n".join([chunk["text"] for chunk in chunks])
    
    prompt = f"""
    You are an expert summarizer. Summarize the following transcript of a YouTube video.
    
    VIDEO TITLE: {metadata.get('title', 'Unknown Title')}
    VIDEO AUTHOR: {metadata.get('author', 'Unknown Author')}
    VIDEO DURATION: {metadata.get('duration', 0)} seconds
    
    TRANSCRIPT:
    {full_transcript}  # Limit transcript length to avoid token limits
    """
    
    # Call the appropriate LLM API based on provider
    try:
        if provider.lower() == "openai":
            return _summarize_with_openai(prompt, summary_func, model)
        elif provider.lower() == "anthropic":
            return _summarize_with_anthropic(prompt, summary_func, model)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    except Exception as e:
        raise RuntimeError(f"Error generating summary with {provider}: {str(e)}")

def _summarize_with_openai(prompt: str, summary_func: BaseModel, model: str = "gpt-4o-mini") -> dict:
    """
    Generate summary using OpenAI API.
    """
    import openai
    import os
    
    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable not set")

    try:
        # Call OpenAI API
        client = openai.OpenAI()
        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert video summarizer."},
                {"role": "user", "content": prompt},
            ],
            response_format=summary_func
        )
        summary = completion.choices[0].message.parsed
        return summary.model_dump()
        
    except Exception as e:
        raise RuntimeError(f"OpenAI API error: {str(e)}")

def _summarize_with_anthropic(prompt: str, summary_func: BaseModel, model: str = "claude-3-5-haiku-latest") -> dict:
    """
    Generate summary using Anthropic API.
    """
    import anthropic
    import json
    import os
    
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model,
            system=f"Your are expert video summarizer. You must respond with JSON that conforms to this schema: {summary_func.model_json_schema()}. Do not include any explanations or text outside the JSON.",
            messages=[
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
        )
        # Extract and parse the response
        summary_text = response.content[0].text
        summary = json.loads(summary_text)
        # Validate the response structure
        _validate_summary_structure(summary)
        return summary
        
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON response from Anthropic API")
    except Exception as e:
        raise RuntimeError(f"Anthropic API error: {str(e)}")


def _validate_summary_structure(summary: dict) -> None:
    """
    Validate that the summary has the expected structure.
    
    Args:
        summary: The summary to validate
        
    Raises:
        ValueError: If the summary structure is invalid
    """
    required_keys = ["tldr", "summary", "tags"]
    for key in required_keys:
        if key not in summary:
            raise ValueError(f"Summary missing required key: {key}")
    
    if not isinstance(summary["tags"], list):
        raise ValueError("tags must be a list")
    
    if not summary["summary"]:
        raise ValueError("detailed_summary cannot be empty")