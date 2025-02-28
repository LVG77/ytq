Below is a comprehensive blueprint along with a series of iterative, test-driven prompt sections. Each section builds on the previous ones so that a code-generation LLM can incrementally produce working code. Every prompt is self-contained, ends with wiring to previous components, and emphasizes testing and best practices.

---

## Overall Project Blueprint

**Project Overview:**  
The goal is to build a CLI tool named **yt-scribe** that processes a single YouTube video URL and outputs a structured JSON summary. The tool will:  
- Download and extract the transcript (using yt-dlp) while preserving timestamps.  
- Chunk the transcript and extract metadata (title, author, video id, duration, etc.).  
- Summarize the transcript using an LLM following a strict JSON template.  
- Generate embeddings for summary bullets.  
- Store data in a hybrid-searchable SQLite database (with tables for videos and transcript chunks).  
- Support a CLI interface (via Typer) for commands like adding a video, querying the database (keyword + semantic search), reprocessing, and displaying summaries.

**Step-by-Step Breakdown:**

1. **Project Setup & File Structure:**  
   - Initialize the repository and virtual environment.  
   - Create a basic file structure with placeholder modules:  
     - `/yt-scribe/__init__.py`  
     - `/yt-scribe/cli.py` (for CLI commands)  
     - `/yt-scribe/core.py` (for transcript download, chunking, and LLM summarization)  
     - `/yt-scribe/db.py` (for database operations)  

2. **Transcript Downloader:**  
   - Implement a function to invoke `yt-dlp` to extract the transcript from a YouTube URL.  
   - Ensure proper error handling (e.g., when a transcript is missing) and add unit tests.

3. **Transcript Chunking & Metadata Extraction:**  
   - Develop logic to split the raw transcript into chunks while preserving timestamps.  
   - Extract video metadata using yt-dlp (title, author, URL, video id, duration).  
   - Write tests that confirm proper chunk creation and metadata extraction.

4. **LLM Summarizer Integration:**  
   - Create a module that sends transcript chunks to an LLM (using a configurable provider) using a strict JSON template.  
   - Validate that the LLM output adheres to the template.  
   - Use mocks to simulate API responses and include unit tests.

5. **Embedding Generation:**  
   - Build a function that takes each summary bullet and generates an embedding via OpenAI/Anthropic APIs (or a simulated version for testing).  
   - Ensure that each bullet maps to exactly one embedding.  
   - Write tests to verify the 1:1 mapping.

6. **Database Schema & CRUD Operations:**  
   - Design an SQLite schema with two tables:  
     - `videos` (with fields: video_id, url, title, author, duration, summary_json, tags, processed_at)  
     - `video_details` (with fields: chunk_id, video_id, chunk_text, embedding, timestamp)  
   - Implement functions for inserting, updating (overwriting on reprocess), and retrieving data.  
   - Develop tests for each database operation.

7. **Query Engine Implementation:**  
   - Implement hybrid search:  
     - Keyword search across `tags` and `chunk_text`.  
     - Semantic search via cosine similarity on the embeddings.  
   - Combine scores to rank results and add tests to verify search accuracy.

8. **CLI Integration with Typer:**  
   - Wire all backend components into CLI commands:  
     - `yts add "video_url"` to process a video.  
     - `yts query "search term"` (with options for semantic search and result limit).  
     - `yts reprocess "video_url"` to refresh data.  
     - `yts summary video_id` to display the summary in markdown.  
   - Include tests using Typer’s testing utilities.

9. **End-to-End Integration Testing:**  
   - Write integration tests that simulate the full flow (add → query → reprocess → summary).  
   - Validate error handling and proper wiring of components.

---

## Iterative Prompts for Code-Generation LLM

Each prompt is self-contained and written as a code block tagged as `text`. Use these prompts sequentially.

---

### **Prompt 1: Project Setup & File Structure**

```text
Create the initial project structure for the yt-scribe CLI tool. The goal is to set up a minimal skeleton that includes:
- A project folder (named "yt-scribe").
- An empty __init__.py file.
- A cli.py file that will later contain CLI commands.
- A core.py file for the transcript download, chunking, and LLM summarization logic.
- A db.py file for database operations.
- A basic README.md file with project description and setup instructions.

At the end, include minimal placeholder code in each Python file (e.g., basic function definitions or Typer CLI app initialization) and add comments indicating where further implementation will follow. Also, include a basic test setup folder (e.g., a tests/ directory with an __init__.py file) for future unit tests.
```

---

### **Prompt 2: Transcript Downloader Module**

```text
Implement a Transcript Downloader module in the core.py file. This module should:
1. Use the yt-dlp library to fetch the transcript of a given YouTube video URL (English transcripts only).
2. Handle both auto-generated and human-made transcripts.
3. Return the raw transcript text along with its timestamps.
4. Raise a clear error if no transcript is found.

Include unit tests (in a new test file, e.g., tests/test_transcript.py) that:
- Verify that the function correctly returns transcript data for a valid URL.
- Check that an appropriate error is raised for videos without transcripts.

Focus on clean error handling and modularity, so that later steps (chunking, metadata extraction) can build upon this function.
```

---

### **Prompt 3: Transcript Chunking & Metadata Extraction**

```text
Expand the core.py module to include functions for:
1. Splitting the raw transcript into manageable chunks (e.g., by sentence or paragraph) while preserving the associated timestamps.
2. Extracting metadata from the video using yt-dlp (including title, author, URL, duration, and video id).

Write unit tests (in tests/test_chunking.py) to ensure:
- The chunking function produces correctly segmented chunks with their timestamps.
- The metadata extraction function returns all required fields in the correct format.

Ensure that the code is modular so that both the transcript and metadata can be used in subsequent LLM summarization and database insertion steps.
```

---

### **Prompt 4: LLM Summarizer Integration**

```text
Create a new function in core.py for LLM summarization. This function should:
1. Accept a transcript (or its chunks) and video metadata as input.
2. Use a configurable LLM provider (e.g., OpenAI or Anthropic) to generate a summary.
3. Use a strict JSON template that includes: title, a 2-3 sentence TLDR, a list of detailed summary bullets (each with text and a timestamp), and tags.
4. Validate that the output adheres to the JSON template.

Include unit tests (in tests/test_llm_summarizer.py) that:
- Use mocks to simulate the LLM API call.
- Verify that the function returns a well-structured JSON summary.
- Test error handling for API timeouts or malformed responses.

Document in comments where the prompt template is used and how the configuration (model and provider) is managed.
```

---

### **Prompt 5: Embedding Generation Module**

```text
Develop an embedding generation function in core.py that:
1. Accepts individual summary bullets (from the detailed summary list) as input.
2. Calls an embedding API (configurable between OpenAI and Anthropic, or a stub for testing) to generate a numeric embedding vector for each bullet.
3. Returns a mapping of each bullet to its corresponding embedding.

Write unit tests (in tests/test_embeddings.py) to:
- Ensure that each summary bullet is processed and exactly one embedding is generated.
- Handle errors gracefully if the API call fails, using a retry mechanism (with a maximum of 2 retries).

Keep the implementation modular so that the embedding function can be integrated later with the database operations.
```

---

### **Prompt 6: SQLite Database Schema & CRUD Operations**

```text
In the db.py module, implement the following:
1. Design an SQLite schema with two tables:
   - A 'videos' table with fields: video_id (PK), url, title, author, duration, summary_json, tags, processed_at.
   - A 'video_details' table with fields: chunk_id (PK), video_id (FK), chunk_text, embedding, timestamp.
2. Write functions for:
   - Inserting a new video record and its corresponding transcript chunks.
   - Updating (overwriting) an existing video's records when reprocessed.
   - Retrieving video and chunk data for queries.

Also, write unit tests (in tests/test_db.py) to:
- Verify that data is inserted correctly.
- Ensure that reprocessing a video overwrites previous entries.
- Test data retrieval operations.

Emphasize safety, clear error messages, and connection management in the database functions.
```

---

### **Prompt 7: Query Engine Implementation**

```text
Implement a Query Engine function in db.py (or a new module, e.g., query.py) that:
1. Accepts a query string and optional flags (such as --semantic and --limit).
2. Performs a keyword search on the 'tags' and 'chunk_text' fields.
3. If the --semantic flag is provided, computes cosine similarity between the query embedding and stored embeddings.
4. Combines keyword match counts and semantic scores to produce a final ranked list of results.
5. Returns formatted results that include the video title, author, a matched bullet with timestamp, and a score.

Write unit tests (in tests/test_query.py) to:
- Validate that both keyword and semantic searches return correct results.
- Test the ranking mechanism.
- Ensure the function handles edge cases (e.g., no matches found).

The function should be designed to integrate with the CLI command for query.
```

---

### **Prompt 8: CLI Integration using Typer**

```text
Integrate all previously built components into a CLI application using Typer in cli.py. The CLI should implement the following commands:
1. `yts add "video_url"` – Processes a video by calling transcript download, chunking, metadata extraction, LLM summarization, embedding generation, and stores data in the database.
2. `yts reprocess "video_url"` – Reprocesses an already processed video and updates the database.
3. `yts query "search term"` – Searches the database using keyword or semantic search, with an option to set a limit.
4. `yts summary video_id` – Displays the video summary in markdown format.
5. Additional commands to display config paths and database paths if needed.

Include basic argument parsing, error handling, and wiring of each CLI command to the appropriate functions from core.py and db.py.

Also, add CLI tests using Typer’s testing utilities (in tests/test_cli.py) to simulate command-line input and verify expected outputs.
```

---

### **Prompt 9: End-to-End Integration Testing**

```text
Write end-to-end integration tests that simulate the entire workflow. In a new file (e.g., tests/test_integration.py), develop tests that:
1. Simulate processing a YouTube video using the `yts add` command.
2. Verify that the transcript is correctly downloaded, chunked, summarized, and stored in the database.
3. Run a query using `yts query` and check that the output includes the expected matched bullet, timestamp, and ranking score.
4. Reprocess a video using `yts reprocess` and verify that old data is properly overwritten.
5. Test the `yts summary` command to ensure the summary is displayed in the correct format.

Ensure that the tests run in an isolated environment (e.g., a temporary database) so that they do not interfere with production data.
```

---

Each prompt is designed to be incremental, self-contained, and test-driven. When implementing, ensure that each new piece of functionality is integrated with the previous components and that no orphaned code is left behind. This series of prompts provides a clear roadmap from setting up the project to delivering a fully integrated and tested yt-scribe CLI tool.