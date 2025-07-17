# AGENTS.md

5. - 我在做一个 Flask + OpenAI Responses API 的项目，里面已有普通问答、图像生成功能以及 Code Interpreter 和历史记录。现在希望增加一个「流式问答」功能，要求如下：
   
     1. **后端**  
        - 在 `app.py` 中新增或修改 `/stream_query` 路由，使其使用 Chat Completions API 的 `stream=True` 流式模式，模型选 `gpt-3.5-turbo`（或 `gpt-4.1`）。  
        - 输出每个 token 时用 SSE 发送格式 `data: {token}\n\n`，结束后发送 `data: [DONE]\n\n`。  
        - 确保 Response header 包含：
          ```
          Content-Type: text/event-stream
          Cache-Control: no-cache
          Connection: keep-alive
          ```
        - 将相关逻辑（读取 `request.args.get("query")`、调用 OpenAI、yield 增量）封装在 `helpers.py` 的 `ai_query_stream` 或 `chat_stream` 中，保持其他工具（file search、codex、image）互不干扰。
   
     2. **前端**  
        - 在 `index.html`（或 `image.html`）中，修改或新增用于流式显示的 `<div id="stream-output"></div>` 和脚本：  
          ```html
          <script>
            const outputDiv = document.getElementById("stream-output");
            const es = new EventSource(`/stream_query?query=${encodeURIComponent(userInput)}`);
            es.onmessage = e => {
              if (e.data === "[DONE]") {
                es.close();
                // 代码块高亮
                document.querySelectorAll('pre code').forEach(block=>hljs.highlightElement(block));
              } else {
                outputDiv.textContent += e.data;
                outputDiv.innerHTML = marked.parse(outputDiv.textContent);
              }
            };
            es.onerror = err => {
              console.error("SSE error", err);
              es.close();
            };
          </script>
          ```
        - 确保页面已经引入了 `marked.min.js` 和 `highlight.min.js`，并在 `<head>` 中正确加载。
   
     3. **依赖 & 配置**  
        - `openai` Python 包版本需 ≥ 0.27.0；  
        - 在 `app.py` 中设置：
          ```python
          app.secret_key = os.getenv("FLASK_SECRET")
          from flask_session import Session
          app.config["SESSION_TYPE"] = "filesystem"
          Session(app)
          ```
        - 如果前端从不同域访问，请加上 `flask-cors`：
          ```python
          from flask_cors import CORS
          CORS(app, supports_credentials=True)
          ```
   
     请直接输出完整修改后的 `app.py`、`helpers.py` 和前端 HTML/JS 片段，保留原有其他功能不变，确保流式问答可以边打字边渲染 Markdown，并自动高亮代码块。谢谢！

---

## 环境配置建议

- **Python 包**  
  ```bash
  pip install -r requirements.txt
  # 确保 openai>=0.27.0，flask-session，requests，markdown，highlight.js

