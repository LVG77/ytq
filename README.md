# yt-scribe

[![PyPI](https://img.shields.io/pypi/v/yt-scribe.svg)](https://pypi.org/project/yt-scribe/)
[![Changelog](https://img.shields.io/github/v/release/lvg77/yt-scribe?include_prereleases&label=changelog)](https://github.com/lvg77/yt-scribe/releases)
[![Tests](https://github.com/lvg77/yt-scribe/actions/workflows/test.yml/badge.svg)](https://github.com/lvg77/yt-scribe/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/lvg77/yt-scribe/blob/master/LICENSE)

Build knowledge base from YouTube video transcripts

## Overview

`yt-scribe` is a CLI tool that processes YouTube videos to create a searchable knowledge base. It:

- Downloads and extracts transcripts from YouTube videos
- Uses LLMs to generate structured summaries
- Creates embeddings for semantic search
- Stores everything in a searchable SQLite database
- Provides a CLI for adding videos, searching, and viewing summaries

## Installation

Install this tool using `pip`:
```bash
pip install yt-scribe
```

If you are using `uv` then you can run directly the cli in temporary enviironment like so:
```bash
uvx yts <command> <args>
```
or you can also install it as a tool:
```bash
uv tool install yt-scribe
# and then
yts <command> <args>
```

## Usage

### Adding a Video to the Knowledge Base

To add a YouTube video to your knowledge base, use the `add` command:

```bash
yts add <video_url>
```

Optional parameters:
- `--chunk-size`: Maximum size of each text chunk (default: 1000 characters)
- `--chunk-overlap`: Overlap between chunks (default: 100 characters)
- `--provider`: LLM summarization provider (default: "openai")
- `--model`: LLM summarization model (default: "gpt-4o-mini")

Example:
```bash
yts add https://youtube.com/watch?v=example --chunk-size 1500 --provider anthropic
```

### Searching the Knowledge Base

Search your knowledge base using the `query` command:

```bash
yts query <search_term>
```

Search options:
- `--chunks`: Enable chunk-level search
- `--semantic`: Enable semantic search (when chunk search is enabled)
- `--limit`: Maximum number of results (default: 3)

Examples:
```bash
# Video-level search (default)
yts query "machine learning"

# Chunk-level keyword search
yts query "neural networks" --chunks

# Semantic chunk-level search
yts query "types of algorithms" --chunks --semantic
```

### Viewing Video Summary

To view a summary of a specific video:

```bash
yts summary <video_id>
```

Example:
```bash
yts summary dQw4w9WgXcQ
```

### Deleting a Video

To remove a video from the knowledge base:

```bash
yts delete <video_id>
```

### Version Information

To check the version of yt-scribe:

```bash
yts --version
```

## Development

To contribute to this tool, first checkout the code. Then create a new virtual environment:
```bash
cd yt-scribe
python -m venv venv
source venv/bin/activate
```

Now install the dependencies and test dependencies:
```bash
pip install -e '.[test]'
```

To run the tests:
```bash
python -m pytest
```
