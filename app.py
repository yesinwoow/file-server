from flask import Flask, render_template_string, send_file, request, jsonify, abort
import os, mimetypes, math

app = Flask(__name__)
ROOT_DIR = "/storage/emulated/0"

def human_size(b):
    if b == 0: return "0 B"
    units = ["B","KB","MB","GB","TB"]
    i = int(math.floor(math.log(b, 1024)))
    return f"{b / 1024**i:.1f} {units[i]}"

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NEXUS FS</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&display=swap');

:root {
  --bg:       #020810;
  --surface:  #060f1e;
  --border:   #0d2137;
  --cyan:     #00f5ff;
  --cyan-dim: #007a8a;
  --magenta:  #ff00a0;
  --yellow:   #ffd700;
  --text:     #a8c8e8;
  --muted:    #3a5a7a;
  --success:  #00ff88;
  --danger:   #ff3366;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Share Tech Mono', monospace;
  min-height: 100vh;
  overflow-x: hidden;
}

/* scanline overlay */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0,245,255,0.015) 2px,
    rgba(0,245,255,0.015) 4px
  );
  pointer-events: none;
  z-index: 999;
}

/* ── header ── */
header {
  padding: 16px 20px 12px;
  border-bottom: 1px solid var(--border);
  background: linear-gradient(180deg, rgba(0,245,255,0.05) 0%, transparent 100%);
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.logo {
  font-family: 'Orbitron', sans-serif;
  font-weight: 900;
  font-size: 1.4rem;
  color: var(--cyan);
  text-shadow: 0 0 20px var(--cyan), 0 0 40px var(--cyan-dim);
  letter-spacing: 4px;
  flex-shrink: 0;
}

.breadcrumb {
  flex: 1;
  color: var(--muted);
  font-size: 0.78rem;
  word-break: break-all;
  min-width: 0;
}
.breadcrumb a { color: var(--cyan); text-decoration: none; }
.breadcrumb a:hover { color: white; }

/* ── toolbar ── */
.toolbar {
  padding: 10px 20px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  border-bottom: 1px solid var(--border);
  align-items: center;
}

.btn {
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.8rem;
  padding: 7px 14px;
  border-radius: 4px;
  border: 1px solid currentColor;
  cursor: pointer;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.15s;
  white-space: nowrap;
}
.btn-cyan  { color: var(--cyan);    background: rgba(0,245,255,0.08); }
.btn-mag   { color: var(--magenta); background: rgba(255,0,160,0.08); }
.btn-green { color: var(--success); background: rgba(0,255,136,0.08); }
.btn:hover { filter: brightness(1.4); box-shadow: 0 0 12px currentColor; }

/* ── upload zone ── */
#upload-panel {
  display: none;
  margin: 12px 20px;
  border: 2px dashed var(--cyan-dim);
  border-radius: 8px;
  padding: 24px;
  text-align: center;
  transition: border-color 0.2s, background 0.2s;
  background: rgba(0,245,255,0.03);
}
#upload-panel.visible { display: block; }
#upload-panel.dragover {
  border-color: var(--cyan);
  background: rgba(0,245,255,0.08);
}
#upload-panel p { color: var(--muted); margin-bottom: 12px; font-size: 0.85rem; }
#file-input { display: none; }
.upload-label {
  cursor: pointer;
  color: var(--cyan);
  border: 1px solid var(--cyan-dim);
  padding: 8px 18px;
  border-radius: 4px;
  font-size: 0.82rem;
  transition: all 0.15s;
  display: inline-block;
}
.upload-label:hover { background: rgba(0,245,255,0.12); }
#upload-progress-wrap { display: none; margin-top: 14px; }
#upload-bar-track {
  background: var(--border);
  border-radius: 4px;
  height: 6px;
  overflow: hidden;
  margin-bottom: 6px;
}
#upload-bar-fill {
  height: 100%;
  width: 0%;
  background: linear-gradient(90deg, var(--cyan), var(--magenta));
  transition: width 0.1s;
}
#upload-status { font-size: 0.78rem; color: var(--text); }

/* ── file grid ── */
.file-list {
  padding: 12px 20px;
}

.back-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  margin-bottom: 6px;
  border: 1px solid var(--border);
  border-radius: 6px;
  text-decoration: none;
  color: var(--muted);
  font-size: 0.85rem;
  transition: all 0.15s;
}
.back-item:hover { border-color: var(--cyan-dim); color: var(--cyan); background: rgba(0,245,255,0.04); }

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  margin-bottom: 6px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  transition: all 0.15s;
  position: relative;
}
.file-item:hover { border-color: var(--cyan-dim); background: rgba(6,15,30,0.9); }
.file-item:hover .file-actions { opacity: 1; }

.file-icon { font-size: 1.2rem; flex-shrink: 0; width: 28px; text-align: center; }

.file-info { flex: 1; min-width: 0; }
.file-name {
  color: var(--text);
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
  text-decoration: none;
  display: block;
}
.file-name:hover { color: var(--cyan); }
.file-meta { color: var(--muted); font-size: 0.72rem; margin-top: 2px; }

.file-actions {
  display: flex;
  gap: 6px;
  opacity: 0;
  transition: opacity 0.15s;
  flex-shrink: 0;
}
.act-btn {
  font-size: 0.72rem;
  padding: 4px 10px;
  border-radius: 3px;
  border: 1px solid currentColor;
  cursor: pointer;
  font-family: 'Share Tech Mono', monospace;
  background: transparent;
  transition: all 0.15s;
}
.act-dl   { color: var(--success); }
.act-play { color: var(--yellow);  }
.act-del  { color: var(--danger);  }
.act-btn:hover { filter: brightness(1.3); background: rgba(255,255,255,0.05); }

/* ── media player ── */
#media-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.88);
  z-index: 100;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(6px);
}
#media-overlay.visible { display: flex; }

#media-box {
  background: var(--surface);
  border: 1px solid var(--cyan-dim);
  border-radius: 10px;
  padding: 20px;
  max-width: 92vw;
  width: 680px;
  box-shadow: 0 0 60px rgba(0,245,255,0.15);
}
#media-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 0.85rem;
  color: var(--cyan);
  margin-bottom: 14px;
  word-break: break-all;
}
#media-player {
  width: 100%;
  border-radius: 6px;
  background: #000;
  max-height: 70vh;
}
#media-close {
  margin-top: 14px;
  display: block;
  width: 100%;
}

/* ── toast ── */
#toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%) translateY(80px);
  background: var(--surface);
  border: 1px solid var(--cyan-dim);
  color: var(--cyan);
  padding: 10px 22px;
  border-radius: 6px;
  font-size: 0.82rem;
  z-index: 200;
  transition: transform 0.3s;
  white-space: nowrap;
}
#toast.show { transform: translateX(-50%) translateY(0); }

/* ── empty ── */
.empty { color: var(--muted); padding: 40px 20px; text-align: center; font-size: 0.85rem; }

/* mobile touch: always show actions */
@media (max-width: 540px) {
  .file-actions { opacity: 1; }
}
</style>
</head>
<body>

<header>
  <div class="logo">◈ NEXUS/FS</div>
  <div class="breadcrumb">
    <a href="/browse/">~</a>
    {% set parts = current_path.split('/') %}
    {% set ns = namespace(acc='') %}
    {% for p in parts %}
      {% if p %}
        {% set ns.acc = ns.acc + '/' + p %}
        &nbsp;/&nbsp;<a href="/browse/{{ ns.acc.lstrip('/') }}">{{ p }}</a>
      {% endif %}
    {% endfor %}
  </div>
</header>

<div class="toolbar">
  <button class="btn btn-cyan" onclick="toggleUpload()">⬆ Upload</button>
  {% if current_path %}
  <a class="btn btn-mag" href="/browse/{{ parent_path }}">⬅ Back</a>
  {% endif %}
  <span style="color:var(--muted);font-size:0.78rem;margin-left:auto;">
    {{ items|length }} item{{ 's' if items|length != 1 else '' }}
  </span>
</div>

<!-- Upload panel -->
<div id="upload-panel" ondragover="onDrag(event,true)" ondragleave="onDrag(event,false)" ondrop="onDrop(event)">
  <p>Drop files here or click to select</p>
  <label class="upload-label" for="file-input">Choose files</label>
  <input type="file" id="file-input" multiple onchange="uploadFiles(this.files)">
  <div id="upload-progress-wrap">
    <div id="upload-bar-track"><div id="upload-bar-fill"></div></div>
    <div id="upload-status"></div>
  </div>
</div>

<!-- File list -->
<div class="file-list">
  {% if not items %}
  <div class="empty">▣ Empty directory</div>
  {% endif %}

  {% for item in items %}
  <div class="file-item">
    <div class="file-icon">{{ item.icon }}</div>
    <div class="file-info">
      {% if item.is_dir %}
        <a class="file-name" href="/browse/{{ item.path }}">{{ item.name }}/</a>
      {% else %}
        <a class="file-name" href="/file/{{ item.path }}" download>{{ item.name }}</a>
      {% endif %}
      <div class="file-meta">
        {% if item.size %}{{ item.size_h }}{% endif %}
        {% if item.ext %} &middot; {{ item.ext.upper() }}{% endif %}
      </div>
    </div>
    <div class="file-actions">
      {% if not item.is_dir %}
        <button class="act-btn act-dl" onclick="dlFile('{{ item.path }}')">↓ DL</button>
        {% if item.playable %}
        <button class="act-btn act-play" onclick="playMedia('{{ item.path }}','{{ item.name }}','{{ item.media_type }}')">▶ Play</button>
        {% endif %}
      {% endif %}
    </div>
  </div>
  {% endfor %}
</div>

<!-- Media overlay -->
<div id="media-overlay" onclick="closeMedia(event)">
  <div id="media-box">
    <div id="media-title"></div>
    <video id="media-player" controls style="display:none"></video>
    <audio id="audio-player" controls style="display:none;width:100%"></audio>
    <button class="btn btn-mag media-close" onclick="closeMediaBtn()">✕ Close</button>
  </div>
</div>

<div id="toast"></div>

<script>
const CURRENT = "{{ current_path }}";

// ── upload ──
function toggleUpload() {
  document.getElementById('upload-panel').classList.toggle('visible');
}
function onDrag(e, enter) {
  e.preventDefault();
  document.getElementById('upload-panel').classList.toggle('dragover', enter);
}
function onDrop(e) {
  e.preventDefault();
  onDrag(e, false);
  uploadFiles(e.dataTransfer.files);
}

function uploadFiles(files) {
  if (!files.length) return;
  const wrap = document.getElementById('upload-progress-wrap');
  const bar  = document.getElementById('upload-bar-fill');
  const stat = document.getElementById('upload-status');
  wrap.style.display = 'block';

  let done = 0;
  const total = files.length;

  Array.from(files).forEach(file => {
    const fd = new FormData();
    fd.append('file', file);
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/upload/' + CURRENT);
    xhr.upload.onprogress = e => {
      if (e.lengthComputable) {
        const pct = Math.round(((done + e.loaded / e.total) / total) * 100);
        bar.style.width = pct + '%';
        stat.textContent = `Uploading ${file.name} … ${pct}%`;
      }
    };
    xhr.onload = () => {
      done++;
      bar.style.width = Math.round(done / total * 100) + '%';
      if (done === total) {
        stat.textContent = `✓ ${total} file(s) uploaded`;
        toast('Upload complete');
        setTimeout(() => location.reload(), 1200);
      }
    };
    xhr.onerror = () => { stat.textContent = `✗ Failed: ${file.name}`; };
    xhr.send(fd);
  });
}

// ── download ──
function dlFile(path) {
  const a = document.createElement('a');
  a.href = '/file/' + path;
  a.download = '';
  a.click();
}

// ── media ──
function playMedia(path, name, type) {
  document.getElementById('media-title').textContent = name;
  const vid = document.getElementById('media-player');
  const aud = document.getElementById('audio-player');
  const url = '/file/' + path;
  if (type === 'video') {
    vid.src = url; vid.style.display = 'block';
    aud.style.display = 'none'; aud.src = '';
  } else {
    aud.src = url; aud.style.display = 'block';
    vid.style.display = 'none'; vid.src = '';
  }
  document.getElementById('media-overlay').classList.add('visible');
}
function closeMedia(e) {
  if (e.target === document.getElementById('media-overlay')) closeMediaBtn();
}
function closeMediaBtn() {
  document.getElementById('media-overlay').classList.remove('visible');
  document.getElementById('media-player').pause();
  document.getElementById('audio-player').pause();
}

// ── toast ──
let toastTimer;
function toast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2800);
}
</script>
</body>
</html>
"""

VIDEO_EXT = {'.mp4','.mkv','.webm','.mov','.avi','.3gp','.flv','.m4v'}
AUDIO_EXT = {'.mp3','.wav','.ogg','.flac','.aac','.m4a','.opus','.wma'}

def file_icon(name, is_dir):
    if is_dir: return '📁'
    ext = os.path.splitext(name)[1].lower()
    if ext in VIDEO_EXT: return '🎬'
    if ext in AUDIO_EXT: return '🎵'
    if ext in {'.jpg','.jpeg','.png','.gif','.webp','.bmp','.svg'}: return '🖼'
    if ext in {'.pdf'}: return '📕'
    if ext in {'.zip','.tar','.gz','.bz2','.xz','.7z','.rar'}: return '🗜'
    if ext in {'.py','.js','.ts','.sh','.c','.cpp','.java','.go','.rs'}: return '💻'
    if ext in {'.txt','.md','.log','.csv','.json','.xml','.yaml','.yml'}: return '📄'
    if ext in {'.apk'}: return '📦'
    return '📎'

@app.route("/")
@app.route("/browse/")
@app.route("/browse/<path:req_path>")
def browse(req_path=""):
    abs_path = os.path.join(ROOT_DIR, req_path)
    if not os.path.exists(abs_path):
        return "Path not found", 404

    raw = []
    try:
        entries = os.listdir(abs_path)
    except PermissionError:
        return "Permission denied", 403

    for name in sorted(entries, key=lambda x: (not os.path.isdir(os.path.join(abs_path, x)), x.lower())):
        full = os.path.join(abs_path, name)
        path = os.path.join(req_path, name).lstrip('/')
        is_dir = os.path.isdir(full)
        ext = os.path.splitext(name)[1].lower() if not is_dir else ''
        try:
            size = os.path.getsize(full) if not is_dir else 0
        except:
            size = 0
        playable = ext in VIDEO_EXT | AUDIO_EXT
        media_type = 'video' if ext in VIDEO_EXT else ('audio' if ext in AUDIO_EXT else '')
        raw.append({
            'name': name,
            'path': path,
            'is_dir': is_dir,
            'ext': ext.lstrip('.') if ext else '',
            'icon': file_icon(name, is_dir),
            'size': size,
            'size_h': human_size(size) if not is_dir else '',
            'playable': playable,
            'media_type': media_type,
        })

    parent_path = os.path.dirname(req_path).lstrip('/')
    return render_template_string(HTML, items=raw, current_path=req_path, parent_path=parent_path)

@app.route("/file/<path:file_path>")
def get_file(file_path):
    full = os.path.join(ROOT_DIR, file_path)
    if not os.path.isfile(full):
        return "File not found", 404
    mime, _ = mimetypes.guess_type(full)
    return send_file(full, mimetype=mime or 'application/octet-stream',
                     as_attachment=request.args.get('dl') == '1')

@app.route("/upload/", methods=["POST"])
@app.route("/upload/<path:req_path>", methods=["POST"])
def upload(req_path=""):
    dest_dir = os.path.join(ROOT_DIR, req_path)
    if not os.path.isdir(dest_dir):
        return jsonify({"error": "Invalid path"}), 400
    files = request.files.getlist('file')
    if not files:
        return jsonify({"error": "No files"}), 400
    saved = []
    for f in files:
        if f.filename:
            safe = os.path.basename(f.filename)
            f.save(os.path.join(dest_dir, safe))
            saved.append(safe)
    return jsonify({"saved": saved})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)