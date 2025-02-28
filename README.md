# yt-scribe

[![PyPI](https://img.shields.io/pypi/v/yt-scribe.svg)](https://pypi.org/project/yt-scribe/)
[![Changelog](https://img.shields.io/github/v/release/lvg77/yt-scribe?include_prereleases&label=changelog)](https://github.com/lvg77/yt-scribe/releases)
[![Tests](https://github.com/lvg77/yt-scribe/actions/workflows/test.yml/badge.svg)](https://github.com/lvg77/yt-scribe/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/lvg77/yt-scribe/blob/master/LICENSE)

Build knowledge base from YouTube video transcripts

## Installation

Install this tool using `pip`:
```bash
pip install yt-scribe
```
## Usage

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
