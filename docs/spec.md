# Spec for `yt-scribe` CLI tool

### **1. Core Requirements**  
- **Input**: Single YouTube video URL (English only).  
- **Output**: Structured JSON summary with timestamps, embeddings, and hybrid-searchable SQLite database.  
- **Key Features**:  
  - Transcript extraction with chunking and timestamp preservation.  
  - LLM-powered summarization with a strict template.  
  - OpenAI/Anthropic embeddings for detailed summary bullets.  
  - Hybrid search (keyword + semantic) with timestamped video links.  

---

### **2. Architecture**  
#### **Components**  
1. **Transcript Downloader**:  
   - Uses `yt-dlp` to fetch English transcripts (auto-generated or human).  
   - Splits raw text into chunks (paragraphs/sentences) with preserved timestamps.  
   - Metadata extraction: Title, Author, URL, Duration, video id (via `yt-dlp`).  

2. **LLM Summarizer**:  
   - **Model**: OpenAI (`gpt-4o-mini`) or Anthropic (`claude-3.7-sonnet`), model and model provider are configurable.  
   - **Prompt Template**:  
     ```  
     "Summarize this technical/informational YouTube video transcript. Follow this JSON structure:  
     {  
       'title': '[Video Title]',  
       'tldr': '[2-3 sentence TLDR]',  
       'detailed_summary': [  
         {'bullet': '[Key point]', 'timestamp': '[HH:MM:SS]'},  
         ...  
       ],  
       'tags': ['tag1', 'tag2', ...]  
     }  
     Focus on technical accuracy. Include timestamps for each bullet."  
     ```  
   - **Output**: Strict JSON adhering to the template.  

3. **Embedding System**:  
   - Generates embeddings for each `detailed_summary` bullet using Anthropic (`voyage-3-lite`) or OpenAI (`text-embedding-3-small`).  
   - Stores embeddings alongside their text chunks and timestamps.  

4. **Database**:  
   - **SQLite Schema**:  
     - `videos` Table:  
       ```  
       video_id (PK) | url | title | author | duration | summary_json | tags | processed_at  
       ```  
     - `video_details` Table:  
       ```  
       chunk_id (PK) | video_id (FK) | chunk_text | embedding | timestamp  
       ```  
   - **Reprocessing**: Overwrites existing entries for a video when reprocessed.  

5. **Query Engine**:  
   - **Hybrid Search**:  
     - Keyword: Matches against `tags` (from summary) and `chunk_text`.  
     - Semantic: Cosine similarity between query embedding and `video_details.embedding`.  
     - Keyword is default. Semantic can be toggled with `--semantic` flag.
     - `--limit`: Max results to return. Defaults to 3.
   - **Ranking**: Combined score (keyword match count + semantic similarity).  

---

### **3. CLI Design**  
#### **Library and CLI names**
- `yt-scribe` (library)
- `yts` (CLI)
#### **Commands**  
```bash  
# Add/process a video  
yts add "https://youtube.com/..."  [--model gpt4o-mini] [--model-provider openai|anthropic]

# Hybrid search (semantic off by default)  
yts query "AI ethics" [--semantic] [--limit 3]  

# Reprocess a video  
yts reprocess "https://youtube.com/..."

# Display markdown summary for a video  
yts summary video_id

# Show path to config
yts --config_path

# Show path to database
yts --path
```  

#### **Output Format**  
Example output for the `yts query 'AI ethics'` command:
```  
Results for "AI ethics":  
1. [Video Title] by [Author] (https://youtu.be/VIDEO_ID?t=123)  
   - Matched bullet: "Ethical implications of neural networks..."
   - Timestamp: [00:12:34] [link to time in video]  
   - Score: 0.87  
2. ...  
```  

---

### **4. Error Handling**  
- **Transcript Errors**:  
  - Skip videos with no transcripts; log: "No transcript found for [URL]".  
- **API Failures**:  
  - Retry 2x for OpenAI/Anthropic timeouts.  
  - Exit with "API error: [reason]" on persistent failures.  
- **Invalid URL**: Validate URL structure upfront; reject non-YouTube URLs.  
- **Empty Queries**: Return "No matches found" with suggestions (e.g., broader keywords).  

---

### **5. Testing Plan**  
#### **Unit Tests**  
- Transcript extraction/chunking (with timestamp preservation).  
- LLM prompt adherence (validate JSON structure, template compliance).  
- Embedding generation (ensure 1:1 mapping of bullets to embeddings).  
- SQLite CRUD operations (reprocessing overwrites old data).  

#### **Integration Tests**  
- End-to-end flow: `add -> query -> reprocess -> query`.  
- Hybrid search accuracy: Validate combined keyword/semantic results.  

#### **CLI Testing**  
- Validate argument parsing (e.g., `--semantic` flag toggles embedding search).  
- Test error messages for invalid URLs, missing transcripts, and API failures.  

---

### **6. Dependencies**  
- Libraries:  
  - `typer` (CLI)
  - `yt-dlp` (transcript/metadata).  
  - `openai`/`anthropic` (LLM + embeddings).  
  - `sqlite3` (database), `numpy` (cosine similarity).  
- Configuration:
  - Config file stored in hidden `~/.yt-scribe` directory.
  - `model` and `model_provider` are configurable in the config file but can also be set as CLI flags.
  - for OpenAI/Anthropic keys first look for `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` environment variables. If not found, fall back to config file.
  - Summarize prompt template stored in `prompt_template` in the config file but can also be set as a CLI flag.
---

### **7. File Structure**:  
  ```  
  /yt-scribe  
    ├── __init__.py  
    ├── cli.py (CLI commands and CLI entrypoint)  
    ├── core.py (transcript/LLM/embedding logic)  
    ├── db.py (database operations)  
  ```  

---

### **8. Future Extensions (Noted)**  
- Plugin extensibility similar to this [llm plugin system](https://llm.datasette.io/en/stable/plugins/tutorial-model-plugin.html)
- Support for other LLM providers.  
- Open-source embedding alternatives (e.g., `sentence-transformers`).  
