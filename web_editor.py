"""
GameScript Web Editor v0.5 — минимальный редактор
Запуск: python web_editor.py
Открыть: http://localhost:5000
"""

from flask import Flask, render_template_string, request
from gamescript.compiler import compile_text

app = Flask(__name__)

HTML = r'''
<!DOCTYPE html>
<html>
<head>
    <title>GameScript Editor</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/monaco-editor@0.44.0/min/vs/editor/editor.main.css">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { display: flex; flex-direction: column; height: 100vh; background: #1e1e1e; touch-action: pan-x pan-y; }
        #toolbar { display: flex; justify-content: center; padding: 8px; background: #252526; border-bottom: 1px solid #3e3e42; }
        #btn-build { padding: 8px 30px; background: #0e639c; color: #fff; border: 1px solid #1177bb; cursor: pointer; border-radius: 4px; font-size: 14px; font-weight: bold; }
        #btn-build:active { background: #1177bb; }
        #editor-pane { flex: 1; min-height: 0; }
        #output-pane { height: 35%; background: #1a1a1a; overflow: auto; padding: 10px 15px; white-space: pre-wrap; font-family: 'Consolas', 'Courier New', monospace; font-size: 12px; border-top: 2px solid #0e639c; color: #ccc; }
        .error { color: #f44747; }
        .success { color: #4ec9b0; }
    </style>
</head>
<body>
    <div id="toolbar">
        <button id="btn-build" onclick="build()">🔨 BUILD (C++)</button>
    </div>
    <div id="editor-pane"></div>
    <div id="output-pane">// Нажми BUILD или Ctrl+Enter</div>

    <script src="https://cdn.jsdelivr.net/npm/monaco-editor@0.44.0/min/vs/loader.js"></script>
    <script>
        document.addEventListener('touchstart', function(e) { if (e.touches.length > 1) e.preventDefault(); }, { passive: false });
        var lastTouchEnd = 0;
        document.addEventListener('touchend', function(e) { var now = Date.now(); if (now - lastTouchEnd <= 300) e.preventDefault(); lastTouchEnd = now; }, false);
        
        require.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.44.0/min/vs' } });
        require(['vs/editor/editor.main'], function() {
            window.editor = monaco.editor.create(document.getElementById('editor-pane'), {
                value: 'HERO = {\n    "name": "Артур",\n    "hp": 100,\n}\n\nclass Hero:\n    def on_create(self):\n        self.hp = HERO.hp\n        print("Hello GameScript!")\n',
                language: 'python',
                theme: 'vs-dark',
                fontSize: 13,
                minimap: { enabled: false },
                automaticLayout: true,
                scrollBeyondLastLine: false,
                mouseWheelZoom: false,
                lineNumbers: 'on',
                tabSize: 4,
                insertSpaces: true,
            });
            
            window.editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, build);
        });
        
        async function build() {
            const output = document.getElementById('output-pane');
            output.innerHTML = '⏳ Building...';
            const code = window.editor.getValue();
            try {
                const resp = await fetch('/compile', { method: 'POST', body: code });
                const text = await resp.text();
                const isErr = text.includes('Ошибка') || text.includes('Error');
                output.innerHTML = (isErr ? '<span class="error">' : '<span class="success">') + text.replace(/</g,'&lt;').replace(/>/g,'&gt;') + '</span>';
            } catch(e) {
                output.innerHTML = '<span class="error">' + e + '</span>';
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/compile', methods=['POST'])
def compile_code():
    code = request.get_data(as_text=True)
    try:
        return compile_text(code)
    except Exception as e:
        return f"Ошибка: {e}"

if __name__ == '__main__':
    print("GameScript Editor → http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)