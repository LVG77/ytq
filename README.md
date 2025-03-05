# ytq

[![PyPI](https://img.shields.io/pypi/v/ytq.svg)](https://pypi.org/project/ytq/)
[![Changelog](https://img.shields.io/github/v/release/lvg77/ytq?include_prereleases&label=changelog)](https://github.com/lvg77/ytq/releases)
[![Tests](https://github.com/lvg77/ytq/actions/workflows/test.yml/badge.svg)](https://github.com/lvg77/ytq/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/lvg77/ytq/blob/master/LICENSE)

Build knowledge base from YouTube video transcripts

## Overview

`ytq` (short for YouTube Query) is a CLI tool that processes YouTube videos to create a searchable knowledge base. It:

- Downloads and extracts transcripts from YouTube videos
- Uses LLMs to generate structured summaries
- Each transcript is split into multiple chunks (subsections). Each section preserves its start and end times timestemps. Then chunks are embedded using openai 'text-embedding-3-small' model. Created embeddings are used when `--semantic` search flag is enabled.
- Stores everything in a searchable SQLite database
- Provides a CLI for adding videos, searching, and viewing summaries

## Installation

Install this tool using `pip`:
```bash
pip install ytq
```

If you are using `uv` then you can run directly the cli in temporary enviironment like so:
```bash
uvx ytq <command> <args>
```
or you can also install it as a tool:
```bash
uv tool install ytq
# and then
ytq <command> <args>
```

## Usage

### Adding a Video to the Knowledge Base

To add a YouTube video to your knowledge base, use the `add` command:

```bash
ytq add <video_url>
```

Optional parameters:
- `--chunk-size`: Maximum size of each text chunk (default: 1000 characters)
- `--chunk-overlap`: Overlap between chunks (default: 100 characters)
- `--provider`: LLM summarization provider (default: "openai")
- `--model`: LLM summarization model (default: "gpt-4o-mini")

Example:
```bash
ytq add https://youtube.com/watch?v=example --chunk-size 1500 --provider anthropic
```
If you try storing a video that is already in the db, the old version is removed and replaced with the new version.

### Searching the Knowledge Base

Search your knowledge base using the `query` command:

```bash
ytq query <search_term>
```

Search options:
- `--chunks`: Enable chunk-level search
- `--semantic`: Enable semantic search (when chunk search is enabled)
- `--limit`: Maximum number of results (default: 3)

Examples:
```bash
# Video-level search (default)
ytq query "machine learning"

# Chunk-level keyword search
ytq query "neural networks" --chunks

# Semantic chunk-level search
ytq query "types of algorithms" --chunks --semantic
```

### Viewing Video Summary

To view a summary of a specific video:

```bash
ytq summary <video_id>
```

Example:
```bash
ytq summary dQw4w9WgXcQ
```

### Deleting a Video

To remove a video from the knowledge base:

```bash
ytq delete <video_id>
```

### Version Information

To check the version of ytq:

```bash
ytq --version
```

## Development

To contribute to this tool, first checkout the code. Then create a new virtual environment:
```bash
cd ytq
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
