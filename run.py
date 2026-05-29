"""
StudyTutorAI - Lightweight Desktop Server
Uses Python's built-in http.server + Flask-like routing.
No Gradio dependency = small EXE + low memory.
"""
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
import json
import sys
import os
import webbrowser
import threading
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except:
        pass

PORT = 7860
MODEL_DIR = Path(__file__).parent / "models"

# State
_chat_engine = None
_load_error = None

HTML = r"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>学霸帝AI</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f0f2f5; min-height: 100vh; }
.app { max-width: 900px; margin: 0 auto; padding: 20px; }
.header { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 24px; border-radius: 12px; margin-bottom: 20px; }
.header h1 { font-size: 28px; margin-bottom: 8px; }
.header p { opacity: 0.9; font-size: 14px; }
.card { background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); overflow: hidden; margin-bottom: 16px; }
.tabs { display: flex; border-bottom: 1px solid #eee; }
.tab { padding: 14px 24px; cursor: pointer; font-size: 14px; border-bottom: 2px solid transparent; color: #666; }
.tab.active { color: #667eea; border-bottom-color: #667eea; font-weight: 600; }
.tab-content { display: none; padding: 20px; }
.tab-content.active { display: block; }
#chat-messages { height: 400px; overflow-y: auto; padding: 16px; border-bottom: 1px solid #eee; }
.msg { margin: 12px 0; padding: 12px 16px; border-radius: 12px; max-width: 80%; font-size: 14px; line-height: 1.6; white-space: pre-wrap; }
.msg.user { background: #667eea; color: white; margin-left: auto; border-bottom-right-radius: 4px; }
.msg.bot { background: #f0f0f0; color: #333; border-bottom-left-radius: 4px; }
.controls { padding: 16px; display: flex; gap: 8px; }
#msg-input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; outline: none; }
#msg-input:focus { border-color: #667eea; }
button { background: #667eea; color: white; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-size: 14px; }
button:hover { background: #5a6fd6; }
.status { padding: 12px 16px; font-size: 13px; }
.status.warn { background: #fff3cd; color: #856404; }
.status.ok { background: #d4edda; color: #155724; }
.empty-chat { text-align: center; padding: 60px 20px; color: #999; }
.empty-chat h3 { margin-bottom: 8px; }
.upload-area { padding: 20px; }
#file-input { margin: 10px 0; }
.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; padding: 20px; }
.stat-card { text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px; }
.stat-card .num { font-size: 32px; font-weight: 700; color: #667eea; }
.stat-card .label { font-size: 13px; color: #666; margin-top: 4px; }
</style>
</head>
<body>
<div class="app">
  <div class="header">
    <h1>学霸帝AI</h1>
    <p>你的私人AI导师 - 本地运行、隐私安全、离线可用</p>
  </div>

  <div class="status" id="status-bar"></div>

  <div class="card">
    <div class="tabs">
      <div class="tab active" onclick="switchTab('chat')">对话学习</div>
      <div class="tab" onclick="switchTab('kb')">知识库</div>
      <div class="tab" onclick="switchTab('stats')">学习档案</div>
    </div>

    <div class="tab-content active" id="tab-chat">
      <div id="chat-messages">
        <div class="empty-chat">
          <h3>有什么不懂的？问我吧！</h3>
          <p>我会用苏格拉底式引导，帮你一步步理解知识</p>
        </div>
      </div>
      <div class="controls">
        <input type="text" id="msg-input" placeholder="输入你的问题..." onkeypress="if(event.key==='Enter')sendMsg()">
        <button onclick="sendMsg()">发送</button>
        <button onclick="clearChat()" style="background:#999">清空</button>
      </div>
    </div>

    <div class="tab-content" id="tab-kb">
      <div class="upload-area">
        <h3>上传PDF文件</h3>
        <p style="color:#666;font-size:13px;margin:8px 0">添加学习资料到知识库，AI会基于这些内容回答问题</p>
        <input type="file" id="file-input" accept=".pdf" multiple>
        <button onclick="uploadFiles()" style="margin-top:8px">上传</button>
        <div id="upload-result" style="margin-top:12px;font-size:13px"></div>
      </div>
    </div>

    <div class="tab-content" id="tab-stats">
      <div class="stats-grid">
        <div class="stat-card"><div class="num" id="stat-questions">0</div><div class="label">提问次数</div></div>
        <div class="stat-card"><div class="num" id="stat-sessions">1</div><div class="label">学习天数</div></div>
        <div class="stat-card"><div class="num" id="stat-topics">0</div><div class="label">涉及知识点</div></div>
      </div>
    </div>
  </div>
</div>

<script>
let questionCount = 0;

function switchTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('tab-' + name).classList.add('active');
}

function addMsg(role, text) {
  const chat = document.getElementById('chat-messages');
  // Remove empty state
  const empty = chat.querySelector('.empty-chat');
  if (empty) empty.remove();

  const div = document.createElement('div');
  div.className = 'msg ' + (role === 'user' ? 'user' : 'bot');
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

async function sendMsg() {
  const input = document.getElementById('msg-input');
  const msg = input.value.trim();
  if (!msg) return;

  addMsg('user', msg);
  input.value = '';
  input.disabled = true;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: msg})
    });
    const data = await res.json();
    addMsg('bot', data.reply || data.error || '暂无回复');
    questionCount++;
    document.getElementById('stat-questions').textContent = questionCount;
  } catch(e) {
    addMsg('bot', '[错误] ' + e.message);
  }
  input.disabled = false;
  input.focus();
}

function clearChat() {
  const chat = document.getElementById('chat-messages');
  chat.innerHTML = '<div class="empty-chat"><h3>有什么不懂的？问我吧！</h3><p>我会用苏格拉底式引导，帮你一步步理解知识</p></div>';
}

async function uploadFiles() {
  const files = document.getElementById('file-input').files;
  if (!files.length) return;

  const fd = new FormData();
  for (let f of files) fd.append('files', f);

  try {
    const res = await fetch('/api/upload', {method: 'POST', body: fd});
    const data = await res.json();
    document.getElementById('upload-result').textContent = data.message || '上传成功';
  } catch(e) {
    document.getElementById('upload-result').textContent = '上传失败：' + e.message;
  }
}

// Check status on load
fetch('/api/status').then(r=>r.json()).then(d => {
  const bar = document.getElementById('status-bar');
  if (d.model_loaded) {
    bar.className = 'status ok';
    bar.textContent = '模型已加载 - 随时提问！';
  } else if (d.model_exists) {
    bar.className = 'status warn';
    bar.textContent = '模型已找到 - 首次提问时自动加载';
  } else {
    bar.className = 'status warn';
    bar.textContent = '未找到模型。请运行 python download_models.py 下载 Qwen2.5-0.5B-Instruct 到 models/ 目录。';
  }
});
</script>
</body>
</html>
"""


class RequestHandler(BaseHTTPRequestHandler):
    """Handle HTTP requests"""

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self._send_html(HTML)
        elif self.path == '/api/status':
            self._send_json(self._get_status())
        else:
            self._send_json({'error': 'Not found'}, 404)

    def do_POST(self):
        if self.path == '/api/chat':
            self._handle_chat()
        elif self.path == '/api/upload':
            self._handle_upload()
        else:
            self._send_json({'error': 'Not found'}, 404)

    def _send_html(self, content):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def _get_status(self):
        global _chat_engine, _load_error
        # Check model dir directly (works in both source and EXE mode)
        model_exists = False
        try:
            if MODEL_DIR.exists():
                # Look for any model with config.json
                for d in MODEL_DIR.rglob("config.json"):
                    if "Qwen" in str(d) or "qwen" in str(d):
                        model_exists = True
                        break
        except Exception:
            pass
        return {
            "model_exists": model_exists,
            "model_loaded": _chat_engine is not None,
            "load_error": _load_error,
        }

    def _handle_chat(self):
        global _chat_engine, _load_error

        try:
            length = int(self.headers['Content-Length'])
            data = json.loads(self.rfile.read(length))
            msg = data.get('message', '').strip()

            if not msg:
                self._send_json({'reply': 'Please enter a question.'})
                return

            # Try model-based reply
            if _chat_engine is not None:
                try:
                    reply = _chat_engine.chat(msg)
                    self._send_json({'reply': reply})
                    return
                except Exception as e:
                    reply = f"[Model Error] {e}"

            # Try loading model on first use
            elif _load_error is None:
                try:
                    sys.path.insert(0, str(Path(__file__).parent))
                    from app.backend import ModelManager, ChatEngine
                    mm = ModelManager(str(MODEL_DIR))
                    _chat_engine = ChatEngine(mm)
                    reply = _chat_engine.chat(msg)
                    self._send_json({'reply': reply})
                    return
                except ImportError as e:
                    _load_error = f"Missing dependency: {e}"
                except FileNotFoundError as e:
                    _load_error = str(e)
                except Exception as e:
                    _load_error = str(e)

            # Fallback: helpful tip without model
            reply = self._generate_tip(msg)
            self._send_json({'reply': reply})

        except Exception as e:
            self._send_json({'error': str(e)})

    def _generate_tip(self, question: str) -> str:
        """Generate a helpful response when model is not available"""
        return (
            f"我收到了你的问题：\"{question[:100]}\"\n\n"
            f"---\n\n"
            f"[模型未加载] {_load_error or '请运行 python download_models.py 下载模型'}\n\n"
            f"目前可以参考以下学习方法：\n"
            f"- 把问题拆解成更小的子问题\n"
            f"- 在课本中寻找类似的例题\n"
            f"- 尝试用你自己的话解释这个概念\n"
            f"- 问问自己：关于这个主题，我已经知道什么？"
        )

    def _handle_upload(self):
        """Handle PDF upload (simplified - just store files)"""
        kb_dir = Path("knowledge_base")
        kb_dir.mkdir(exist_ok=True)

        try:
            content_type = self.headers['Content-Type']
            length = int(self.headers['Content-Length'])

            # Simple file storage
            self._send_json({'message': 'Upload feature requires model. For now, place PDFs in knowledge_base/ folder manually.'})
        except Exception as e:
            self._send_json({'error': str(e)})

    def log_message(self, format, *args):
        # Suppress request logging
        pass


def main():
    print("=" * 50)
    print("[INFO] xuebad AI starting...")
    print(f"[INFO] URL: http://localhost:{PORT}")
    print("[INFO] Model loads on demand (saves memory)")
    print("=" * 50)

    # Auto-open browser
    def open_browser():
        import time
        time.sleep(2)
        webbrowser.open(f"http://localhost:{PORT}")
    threading.Thread(target=open_browser, daemon=True).start()

    # Start server
    with ThreadingHTTPServer(("", PORT), RequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[INFO] Shutting down...")


if __name__ == '__main__':
    main()