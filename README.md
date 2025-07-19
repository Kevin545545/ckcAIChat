# ckcAIChat 

### Video Demo

*(Add a link or embed GIF once recorded, e.g. `https://.../demo.mp4`)*

## Getting Started

Start by cloning this repository to your local machine:

```bash
git clone https://github.com/Kevin545545/ckcAIChat.git
```

## Setting Up the Development Environment

The project targets **Python 3.10+**.
For a full package list see `requirements.txt`.

Create an isolated env, install deps, and activate (Anaconda):

```
conda create -n ckcAIChat python=3.12
conda activate ckcAIChat
pip install -r requirements.txt
```

## Configuring Your OpenAI API Key

Set the environment variable `OPENAI_API_KEY` in your shell startup file (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
export OPENAI_API_KEY="xxxx"
```

After reloading the shell, run `flask run` and navigate to `http://localhost:5000` to start exploring **ckcAIChat**.

------

### 1. Project Overview

*My first project on github.*

**ckcAIChat** is a multi‑modal, full‑stack AI assistant platform built with Flask + Socket.IO on the backend and a lightweight, responsive Bootstrap/Bootswatch themed frontend. It integrates fast general chat, advanced reasoning, web search, image generation & editing, a sandboxed code interpreter, persistent conversation history, and a newly added **Realtime Voice Conversation** module that delivers low‑latency, bidirectional speech interaction. The project originated as my CS50 final project and evolved quickly over roughly two weeks of iterative debugging, design experiments, and extensive prompt engineering—even though large parts of the raw code scaffolding were AI assisted, considerable time went into architecture decisions, polishing user experience, and resolving subtle concurrency and streaming issues. 

### 2. Motivation & Design Choices

Initially I was uncertain what to build; the idea crystallized around offering a *unified* interface that showcases distinct OpenAI capabilities (fast chat, reasoning, vision, image, code execution, and realtime audio) in a coherent UX rather than isolated demos. 
 A calm light‑blue Bootswatch theme was selected both for aesthetic preference (“light blue is my favourite colour”) and to signal a modern, focused ambience aligned with an AI assistant. 

### 3. Core Feature Set

#### (a) Homepage – General Chat & Reasoning Toggle

The homepage offers a *fast* conversational model for everyday dialogue plus a **Reasoning** checkbox that switches to a more powerful reasoning model for complex, multi‑step tasks; this separation optimizes latency for simple queries while still enabling deeper chains of thought when explicitly required. It also has a Web research checkbox to connect to the Internet and catch the latest news.

It supports file input (PDF / images) so the model can parse and ground its responses in user‑provided documents, consistent with the stated design goal of handling “pdf or image files, automatically parse them and read them.” 
 Streaming token output is enabled to mimic familiar “type‑out” effects and improve perceived responsiveness. 

#### (b) Image Generation & Editing

A dedicated interface (`image.html`) maintains an instruction + history pane: users can generate new images or apply edit prompts (e.g. “Change the background...”) while the system tracks “image generation memories” to give continuity. 
 Content moderation or restricted prompt handling returns an apology page—preserving safety and clarity of failure modes. 

#### (c) Code Interpreter

The code interpreter allows uploading heterogeneous file types (CSV, PDF, images, PowerPoint, etc.) and can itself create new artifacts during analysis—supporting debugging, data analysis, and mathematical computation via a Python execution sandbox. 

#### (d) History Persistence

A unified history view aggregates all conversations (text and image outputs) except the realtime voice sessions, and preserves Markdown formatting so previously generated content renders cleanly. 

#### (e) **Realtime Voice Conversation**

This is the most exciting part and most impressive feature in ckcAIChat. 

### 4. Realtime Conversation – Detailed Description

**Objective:** Deliver natural, low‑friction, half‑duplex (auto turn‑taking) speech interaction where the user speaks freely; the AI detects end‑of‑speech, streams text + audio deltas, and replies with synthesized voice while displaying incremental subtitles.

**Client Flow:**

1. Microphone capture uses the Web Audio API (initially via `ScriptProcessorNode`) to buffer PCM frames.
2. Audio is normalized / (re)sampled to 24 kHz PCM16 and chunked at a short interval (≈50 ms) to balance latency vs. overhead.
3. Chunks emit over a Socket.IO channel to the Flask server; a minimal state tracks whether uncommitted audio exists.
4. A **Force Stop** control allows the user to end the current turn early (e.g., to cut off rambling) and immediately request a response.
5. A **Disconnect** control performs a *graceful* teardown: signals a `stop_event`, drains pending queue items, closes the upstream websocket with code 1000, and notifies the frontend so heartbeat (ping/pong) logging stops.

**Server Flow:**

1. For each Socket.IO session ID, a background event loop + queue + `stop_event` + websocket reference is created (or reused if already active). 
2. The server proxies audio buffer append / commit events to the OpenAI Realtime endpoint, enabling server‑side VAD (`turn_detection: server_vad`) to determine speech boundaries automatically.
3. Incoming Realtime events are fanned out to the client:
   - `response.text.delta` & `response.audio_transcript.delta` → incremental assistant transcript (displayed in a single updating line).
   - `response.audio.delta` → base64 PCM frames aggregated client‑side into a WAV blob for near‑continuous playback.
   - VAD events (`speech_started` / `speech_stopped`) update UI state; `input_audio_buffer.committed` marks a new sealed user turn.
4. On `response.done` or `response.audio.done`, playback is finalized; subsequent user speech resets the incremental line, allowing a clean conversational rhythm.

**UX Decisions:**

- *Single dynamic assistant line* avoids vertical log spam while keeping timing transparent.
- *Force Stop threshold* (minimum buffered ms) prevents accidental zero‑length commits that generate empty responses.
- *Graceful close* avoids orphaned pings that previously persisted after perceived “end of chat.”
- *Semantic color + subtle card highlight* improves readability and focus (blue accent consistent with overall theme). 

**Benefits:** Faster perceived latency, natural pause handling (no manual “send” button), and a foundation for future continuous / interruptible speech (e.g., live barge‑in or barge‑out) with minimal architectural change.

### 5. File & Directory Structure

Below each listed item adds clarifying purpose beyond the succinct original bullets while preserving their intent.

| Path / File                       | Description                                                  |
| --------------------------------- | ------------------------------------------------------------ |
| `app.py`                          | Flask application entry point: different routes, initializes Socket.IO, manages realtime session lifecycle (queues, stop events, graceful websocket closure), dispatches model requests, and aggregates history persistence logic. |
| `helpers.py`                      | Utility functions for common tasks (e.g., formatting, error responses, model wrapper calls). |
| `templates/layout.html`           | Base layout (Bootswatch theme) establishing navigation, shared scripts, and consistent visual hierarchy. |
| `templates/index.html`            | Homepage chat UI: fast model stream area, reasoning toggle, file upload zone, streaming renderer. |
| `templates/image.html`            | Image generation + editing interface with instruction history and moderation fallback linkage. |
| `templates/code_interpreter.html` | Interface for uploading multi‑type files and viewing execution / analysis outputs produced by the Python sandbox. |
| `templates/history.html`          | Aggregates non‑realtime conversation artifacts (text, images) while rendering Markdown appropriately. |
| `templates/realtime.html`         | Realtime voice conversation page: audio capture controls, meters, incremental assistant line, playback audio element. |
| `templates/apology.html`          | User‑facing moderation or error notice page.                 |
| `static/css/`                     | Stylesheets extracted from inline `<style>` (e.g., semantic color variables, dark‑mode overrides) for cache efficiency and CSP hardening. |
| `static/js/`                      | Frontend logic (e.g., realtime chunk handling, incremental transcript merging, force stop/disconnect event wiring). |
| `images/`                         | Stores image assets referenced by Progress.md                |
| `temp_files/`                     | Temp files generated by code interpreter (analysis outputs, transformed files). |
| `Progress.md`                     | Tracks iterative development notes.                          |
| `README.md`                       | Project documentation (this file), elaborating system design, rationale, and usage expectations. |
| `AGNETS.md`                         | Instructions for Codex.                                      |
| `requirements.txt`                  | All the required packages for enviroment                     |

### 6. Usage & Interaction Flow (High Level)

1. **General Chat:** Enter prompt → observe streaming tokens → optionally upload reference files. (Streaming)
2. **Reasoning Mode:** Enable checkbox before sending a complex query (No streaming, slower but deeper). 
3. **Web Search:** Enable checkbox to connect the Internet. (Streaming)
4. **Image Generation:** Provide textual instructions; for edits, reference existing outputs to apply transformations. (No streaming)
5. **Code Interpreter:** Upload data / code → system executes Python tasks and renders outputs or generated files. (No streaming)
6. **Realtime Voice:** Click *Start* → speak → automatic VAD commit → hear synthesized reply; use *Force Stop* for early commit or *Disconnect* for full teardown (prevent lingering heartbeats).
7. **History:** Review non‑realtime artifact timeline; reopen context for follow‑up prompts. 

### 7. Future Enhancements

- AudioWorklet migration for lower latency and better scheduling.
- Barge-in interruption for mid-response user input.
- Multi-voice or adaptive voice style selection.
- Unified vector store for document-based retrieval.
- Role-based memory segmentation and session import/export.
- Streaming for all modules (conversation, search, reasoning, image).
- Improved Markdown parsing in conversation history view.
- Integration of new OpenAI APIs (e.g., Deep Search, File Search).

## License

This project is licensed under the [MIT License](LICENSE).