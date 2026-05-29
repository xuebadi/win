"""
StudyTutorAI - Minimal HTTP Server (No Gradio)
"""
import http.server
import socketserver
import json
from pathlib import Path

PORT = 7860

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>StudyTutorAI</title>
    <style>
        body { font-family: Arial; max-width: 800px; margin: 20px auto; padding: 20px; }
        #chat { height: 400px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; margin: 10px 0; }
        .msg { margin: 10px 0; padding: 10px; border-radius: 8px; }
        .user { background: #e3f2fd; text-align: right; }
        .assistant { background: #f5f5f5; }
        #input { width: 100%; padding: 10px; }
        button { padding: 10px 20px; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>StudyTutorAI</h1>
    <div id="chat"></div>
    <input type="text" id="input" placeholder="Type your question...">
    <button onclick="send()">Send</button>

    <script>
        async function send() {
            const input = document.getElementById('input');
            const msg = input.value.trim();
            if (!msg) return;

            addMessage('user', msg);
            input.value = '';

            const res = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: msg})
            });
            const data = await res.json();
            addMessage('assistant', data.reply);
        }

        function addMessage(role, text) {
            const chat = document.getElementById('chat');
            const div = document.createElement('div');
            div.className = 'msg ' + role;
            div.textContent = text;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        document.getElementById('input').addEventListener('keypress', e => {
            if (e.key === 'Enter') send();
        });
    </script>
</body>
</html>
"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(HTML.encode('utf-8'))

    def do_POST(self):
        if self.path == '/chat':
            length = int(self.headers['Content-Length'])
            data = json.loads(self.rfile.read(length))
            msg = data.get('message', '')

            # Simple echo reply (replace with model later)
            reply = f"[Echo] You said: {msg}"

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'reply': reply}).encode('utf-8'))

    def log_message(self, format, *args):
        pass  # Suppress logging


if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"StudyTutorAI running at http://localhost:{PORT}")
        httpd.serve_forever()