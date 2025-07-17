### 1. Discovery & Hierarchy

Codex will merge AGENTS.md files from global to local scope:

1. `~/.codex/AGENTS.md` (global user overrides)
2. `AGENTS.md` at repo root (project‐wide)
3. `templates/` or subfolder/AGENTS.md (feature‐specific) [GitHub](https://github.com/openai/codex?utm_source=chatgpt.com)

### 2. Project Structure

- **app.py** – Flask routes (`/query`, `/stream_query`, `/generate_image`, `/code_interpreter`, `/history`)
- **helpers.py** – Tool wrappers (ai_query, ai_query_stream, image_generate, code_interpreter_query)
- **templates/** – Jinja2 views (`index.html`, `history.html`, `image.html`)
- **static/** – Client assets (marked.js, highlight.js, SSE JS)

### 3. Coding Conventions

- **Python**
  - Use **Black** (88 chars) for auto-formatting [DataCamp](https://www.datacamp.com/tutorial/openai-codex?utm_source=chatgpt.com)
  - Type‐hint all functions in `helpers.py`
  - Prefix internal helpers with `_`, public API exports without underscore
- **JavaScript**
  - ES6 modules, `const`/`let` over `var`
  - Async/await for fetch calls, SSE using `EventSource` or `ReadableStream` readers
- **Markdown Rendering**
  - Always escape raw user content; use `marked.parse` on stored markdown only

### 4. Testing & Validation

- **Unit Tests**
  - Run `pytest` before finalizing any PR [DataCamp](https://www.datacamp.com/tutorial/openai-codex?utm_source=chatgpt.com)
  - Mock OpenAI client in tests (use `pytest-mock`)
- **Integration Tests**
  - Spin up Flask test server (`pytest --maxfail=1 --disable-warnings -q`)
  - Exercise `/query`, `/stream_query`, `/generate_image`, `/code_interpreter` endpoints
- **Linting**
  - `flake8 .` must pass with zero errors
  - No new warnings in CI logs

### 5. Pull Request Guidelines

- **Title**: `[Feature]` or `[Fix]` short description
- **Description**:
  1. One‐line summary
  2. Motivation & context
  3. Testing steps (include curl or JS snippet)
- **Review**:
  - Attach screenshot or GIF for UI changes
  - Include sample SSE stream logs

### 6. Tooling & Environment

- **OpenAI SDK**: Python `openai>=0.27.0` for Responses & Chat APIs [OpenAI平台](https://platform.openai.com/docs/codex?utm_source=chatgpt.com)
- **Containers**: For Code Interpreter, prefer **auto** mode; reuse a single container per session to avoid exhaustion [OpenAI平台](https://platform.openai.com/docs/guides/agents?utm_source=chatgpt.com)
- **Credentials**:
  - Set `OPENAI_API_KEY` in env
  - `FLASK_SECRET_KEY` for sessions

### 7. Feature‐Specific Notes

#### 7.1 Streaming Chat (`/stream_query`)

- Use **Chat Completions** with `stream=True` (models: gpt-4.1-nano) [OpenAI平台](https://platform.openai.com/docs/guides/agents?utm_source=chatgpt.com)
- SSE format: `data: <token>\n\n`; end with `data: [DONE]\n\n`
- Frontend may fallback to non‐streaming `/query` when `web_search` or `reasoning` is enabled or a file is uploaded

#### 7.2 Web Search & Reasoning

- Enabled via query parameters `?web_search=1` and `?reasoning=1`

- Routed through `client.responses.create` with tool specs:

  ```
  js
  
  
  复制编辑
  tools: [{ type:"web_search_preview" }]
  ```

- Use `previous_response_id` to maintain context across turns

#### 7.3 File Uploads

- Upload via `client.files.create(purpose="user_data")`, pass `file_id` into tool container [OpenAI平台](https://platform.openai.com/docs/guides/agents?utm_source=chatgpt.com)

#### 7.4 Code Interpreter

- Use `code_interpreter` tool in `client.responses.create({"type":"code_interpreter","container":{"type":"auto"}})`
- Reuse same container by storing `container_id` in session; refresh if 404 [OpenAI平台](https://platform.openai.com/docs/guides/agents?utm_source=chatgpt.com)

#### 7.5 Image Generation

- Two modes: `/generate_image` (sync) and `/stream_generate_image` (if using streaming tool call)

- Tool config:

  ```
  js
  
  
  复制编辑
  tools: [{ type:"image_generation", quality:"low", moderation:"low" }]
  ```