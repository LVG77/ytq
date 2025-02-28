# TODO: yt-scribe Project Checklist

This checklist outlines every step needed to build and test the yt-scribe CLI tool.

---

## 1. Project Setup
- [ ] **Initialize Repository & Environment**
  - [ ] Initialize a Git repository.
  - [ ] Set up a virtual environment.
- [ ] **Project Structure**
  - [ ] Create a `yt-scribe/` folder containing:
    - [ ] `__init__.py`
    - [ ] `cli.py` – CLI commands will be implemented here.
    - [ ] `core.py` – Transcript processing, LLM summarization, and embedding logic.
    - [ ] `db.py` – Database schema and CRUD operations.
  - [ ] Create a `tests/` folder with:
    - [ ] `__init__.py`
    - [ ] Placeholder test files for each module (e.g., `test_transcript.py`, `test_chunking.py`, etc.)
- [ ] **Documentation & Dependencies**
  - [ ] Create a `README.md` with project description and setup instructions.
  - [ ] Dependencies to `pyproject.toml`:
    - yt-dlp
    - typer
    - openai and/or anthropic
    - numpy (if needed for cosine similarity)
    - (Other dependencies as required)

---

## 2. Transcript Downloader Module
- [ ] **Implementation in `core.py`**
  - [ ] Write a function that uses `yt-dlp` to fetch the YouTube transcript.
  - [ ] Support English transcripts (auto-generated or human).
  - [ ] Return the raw transcript text along with timestamps.
  - [ ] Implement error handling for cases where no transcript is found.
- [ ] **Testing**
  - [ ] Create tests in `tests/test_transcript.py` to:
    - Verify correct transcript retrieval for valid URLs.
    - Confirm that a clear error is raised for videos without transcripts.

---

## 3. Transcript Chunking & Metadata Extraction
- [ ] **Transcript Chunking**
  - [ ] Develop a function to split the transcript into manageable chunks (e.g., by sentence or paragraph).
  - [ ] Ensure that each chunk retains its associated timestamp.
- [ ] **Metadata Extraction**
  - [ ] Use `yt-dlp` to extract video metadata: title, author, URL, duration, and video id.
- [ ] **Testing**
  - [ ] Write tests in `tests/test_chunking.py` to:
    - Verify that chunks are correctly created with timestamps.
    - Confirm that metadata is accurately extracted and formatted.

---

## 4. LLM Summarizer Integration
- [ ] **LLM Summarization Function**
  - [ ] Implement a function in `core.py` that:
    - Accepts transcript chunks and video metadata.
    - Uses a configurable LLM (e.g., OpenAI or Anthropic) to generate a summary.
    - Adheres to a strict JSON template with:
      - Title
      - A 2-3 sentence TLDR
      - Detailed summary bullets (with timestamps)
      - Tags
  - [ ] Validate that the output conforms to the template.
- [ ] **Testing**
  - [ ] Write unit tests in `tests/test_llm_summarizer.py` using mocks to simulate the LLM API.
  - [ ] Test for correct JSON structure and error handling (e.g., API timeouts).

---

## 5. Embedding Generation Module
- [ ] **Embedding Function**
  - [ ] Create a function in `core.py` to generate embeddings for each summary bullet.
  - [ ] Support a configurable embedding provider (OpenAI/Anthropic or a stub for testing).
  - [ ] Implement a retry mechanism (max 2 retries) in case of API failures.
  - [ ] Ensure a 1:1 mapping between summary bullets and embeddings.
- [ ] **Testing**
  - [ ] Write tests in `tests/test_embeddings.py` to:
    - Verify each bullet generates exactly one embedding.
    - Test error handling for failed API calls.

---

## 6. SQLite Database Schema & CRUD Operations
- [ ] **Database Schema Design**
  - [ ] Create an SQLite schema with:
    - A `videos` table:
      - Fields: video_id (PK), url, title, author, duration, summary_json, tags, processed_at.
    - A `video_details` table:
      - Fields: chunk_id (PK), video_id (FK), chunk_text, embedding, timestamp.
- [ ] **Database Functions**
  - [ ] Implement functions in `db.py` to:
    - Insert new video records and corresponding transcript chunks.
    - Update (overwrite) existing video records during reprocessing.
    - Retrieve video and chunk data for queries.
- [ ] **Testing**
  - [ ] Write tests in `tests/test_db.py` to:
    - Verify correct insertion and retrieval of data.
    - Ensure that reprocessing correctly overwrites previous data.
    - Test error handling and connection management.

---

## 7. Query Engine Implementation
- [ ] **Query Engine Functionality**
  - [ ] Implement a function (in `db.py` or a new module like `query.py`) that:
    - Accepts a query string and optional flags (`--semantic` and `--limit`).
    - Performs a keyword search on `tags` and `chunk_text`.
    - If `--semantic` is enabled, computes cosine similarity between query embeddings and stored embeddings.
    - Combines keyword match counts and semantic scores to rank results.
    - Returns formatted results including video title, author, matched bullet, timestamp, and score.
- [ ] **Testing**
  - [ ] Write tests in `tests/test_query.py` to:
    - Validate the search functionality for both keyword and semantic queries.
    - Check the accuracy of the ranking mechanism.
    - Handle edge cases (e.g., no matches found).

---

## 8. CLI Integration using Typer
- [ ] **CLI Command Implementation in `cli.py`**
  - [ ] Implement the following CLI commands:
    - `yts add "video_url"` – Process a new video.
    - `yts reprocess "video_url"` – Reprocess an existing video.
    - `yts query "search term"` – Search the database (supporting both keyword and semantic search).
    - `yts summary video_id` – Display the video summary in Markdown.
    - [ ] Additional commands for displaying configuration and database paths.
  - [ ] Wire each CLI command to the appropriate functions in `core.py` and `db.py`.
- [ ] **Testing**
  - [ ] Write tests in `tests/test_cli.py` using Typer’s testing utilities to simulate CLI inputs and verify outputs.

---

## 9. End-to-End Integration Testing
- [ ] **Integration Tests**
  - [ ] Create tests in `tests/test_integration.py` to simulate the full workflow:
    - Simulate running `yts add` to process a video.
    - Verify transcript download, chunking, summarization, and database insertion.
    - Simulate running `yts query` and verify correct search results.
    - Simulate running `yts reprocess` and confirm that old data is overwritten.
    - Simulate running `yts summary` and validate the markdown output.
  - [ ] Ensure tests run in an isolated environment (e.g., using a temporary database).

---

## 10. Documentation & Final Testing
- [ ] **Documentation**
  - [ ] Update `README.md` with detailed setup, configuration, and usage instructions.
  - [ ] Document configuration options (API keys, model/provider selection, etc.).
- [ ] **Final Testing**
  - [ ] Run all unit and integration tests.
  - [ ] Perform manual testing of each CLI command.
  - [ ] Validate robust error handling and logging throughout the project.
