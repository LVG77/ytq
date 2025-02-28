# yt-scribe

[![PyPI](https://img.shields.io/pypi/v/yt-scribe.svg)](https://pypi.org/project/yt-scribe/)
[![Changelog](https://img.shields.io/github/v/release/lvg77/yt-scribe?include_prereleases&label=changelog)](https://github.com/lvg77/yt-scribe/releases)
[![Tests](https://github.com/lvg77/yt-scribe/actions/workflows/test.yml/badge.svg)](https://github.com/lvg77/yt-scribe/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/lvg77/yt-scribe/blob/master/LICENSE)

Build knowledge base from YouTube video transcripts

## Overview

yt-scribe is a CLI tool that processes YouTube videos to create a searchable knowledge base. It:

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

## Usage

### Add a video to the knowledge base:
```bash
yt-scribe add "https://youtube.com/watch?v=VIDEO_ID"
```

### Search the knowledge base:
```bash
yt-scribe query "search term"
```

### Enable semantic search:
```bash
yt-scribe query "search term" --semantic
```

### Reprocess a video:
```bash
yt-scribe reprocess "https://youtube.com/watch?v=VIDEO_ID"
```

### Display a video summary:
```bash
yt-scribe summary VIDEO_ID
```

For help, run:
```bash
yt-scribe --help
```

You can also use:
```bash
python -m yt_scribe --help
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
