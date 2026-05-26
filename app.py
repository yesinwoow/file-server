from flask import Flask, render_template_string, send_file, request, jsonify
import os, mimetypes, math, socket

app = Flask(__name__)

ROOTS = {
    "internal": "/storage/emulated/0",
    "sdcard":   "/storage/3CBE-B049",
}

def human_size(b):
    if b == 0: return "0 B"
    units = ["B","KB","MB","GB","TB"]
    i = int(math.floor(math.log(b, 1024)))
    return f"{b / 1024**i:.1f} {units[i]}"

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# ─────────────────────────────────────────────
#  HOME PAGE
# ─────────────────────────────────────────────
HOME_HTML = r"""<!DOCTYPE html>
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
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Share Tech Mono', monospace;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 28px;
  padding: 24px;
}

body::before {
  content: '';
  position: fixed;
  inset: 0;
  background: repeating-linear-gradient(
    0deg, transparent, transparent 2px,
    rgba(0,245,255,0.015) 2px, rgba(0,245,255,0.015) 4px
  );
  pointer-events: none;
  z-index: 999;
}

.logo {
  font-family: 'Orbitron', sans-serif;
  font-weight: 900;
  font-size: 2.2rem;
  color: var(--cyan);
  text-shadow: 0 0 20px var(--cyan), 0 0 60px var(--cyan-dim);
  letter-spacing: 6px;
  text-align: center;
}

.subtitle {
  color: var(--muted);
  font-size: 0.75rem;
  letter-spacing: 3px;
  text-align: center;
  margin-top: -16px;
}

/* Storage cards */
.cards {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  justify-content: center;
}

.card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 28px 40px;
  border: 1px solid var(--cyan-dim);
  border-radius: 10px;
  background: var(--surface);
  text-decoration: none;
  color: var(--text);
  font-size: 0.9rem;
  transition: all 0.2s;
  min-width: 180px;
}
.card:hover {
  border-color: var(--cyan);
  box-shadow: 0 0 28px rgba(0,245,255,0.2);
  color: var(--cyan);
  transform: translateY(-2px);
}
.card-icon { font-size: 2.4rem; }
.card-label { color: inherit; font-size: 0.88rem; letter-spacing: 1px; }
.card-path { color: var(--muted); font-size: 0.68rem; margin-top: 2px; }

/* QR + link box */
.share-box {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 28px;
  text-align: center;
  background: var(--surface);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  width: 100%;
  max-width: 340px;
}

.share-label {
  color: var(--muted);
  font-size: 0.7rem;
  letter-spacing: 2px;
}

/* QR Code canvas */
#qr-canvas {
  border: 3px solid var(--cyan);
  border-radius: 8px;
  padding: 6px;
  background: white;
  box-shadow: 0 0 24px rgba(0,245,255,0.3);
  image-rendering: pixelated;
}

.share-url {
  color: var(--cyan);
  font-size: 0.85rem;
  letter-spacing: 1px;
  word-break: break-all;
}

.copy-btn {
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.75rem;
  padding: 6px 16px;
  border-radius: 4px;
  border: 1px solid var(--cyan-dim);
  cursor: pointer;
  color: var(--cyan);
  background: rgba(0,245,255,0.07);
  transition: all 0.15s;
  letter-spacing: 1px;
}
.copy-btn:hover { background: rgba(0,245,255,0.15); box-shadow: 0 0 10px var(--cyan-dim); }

#copy-ok {
  font-size: 0.72rem;
  color: var(--success);
  height: 14px;
  transition: opacity 0.3s;
  opacity: 0;
}
#copy-ok.show { opacity: 1; }
</style>
</head>
<body>

<div class="logo">◈ NEXUS/FS</div>
<div class="subtitle">MOBILE FILE SYSTEM NAVIGATOR</div>

<div class="cards">
  <a class="card" href="/browse/internal/">
    <div class="card-icon">📱</div>
    <div class="card-label">Internal Storage</div>
    <div class="card-path">/storage/emulated/0</div>
  </a>
  <a class="card" href="/browse/sdcard/">
    <div class="card-icon">💾</div>
    <div class="card-label">SD Card</div>
    <div class="card-path">/storage/3CBE-B049</div>
  </a>
</div>

<div class="share-box">
  <div class="share-label">◈ NETWORK QR CODE</div>
  <canvas id="qr-canvas" width="160" height="160"></canvas>
  <div class="share-url" id="share-url-text">{{ share_url }}</div>
  <button class="copy-btn" onclick="copyLink()">⧉ COPY LINK</button>
  <div id="copy-ok">✓ Copied!</div>
</div>

<!-- Tiny self-contained QR generator (no CDN needed) -->
<script>
// ── Minimal QR Code generator (pure JS, no library needed) ──
// Uses the qrcodejs algorithm reimplemented inline
// For a zero-dependency approach we build the QR matrix ourselves.
// Since full QR is complex, we use a CDN script (loaded below) with fallback.

const SHARE_URL = {{ share_url | tojson }};
document.getElementById('share-url-text').textContent = SHARE_URL;

function copyLink() {
  navigator.clipboard.writeText(SHARE_URL).then(() => {
    const el = document.getElementById('copy-ok');
    el.classList.add('show');
    setTimeout(() => el.classList.remove('show'), 2000);
  });
}

// Load QRCode.js from CDN and draw
(function() {
  const script = document.createElement('script');
  script.src = 'https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js';
  script.onload = drawQR;
  script.onerror = drawFallback;
  document.head.appendChild(script);
})();

function drawQR() {
  const canvas = document.getElementById('qr-canvas');
  // QRCode.js doesn't draw to existing canvas easily; use a temp div
  const tmp = document.createElement('div');
  tmp.style.display = 'none';
  document.body.appendChild(tmp);

  new QRCode(tmp, {
    text: SHARE_URL,
    width: 148,
    height: 148,
    colorDark: '#003344',
    colorLight: '#ffffff',
    correctLevel: QRCode.CorrectLevel.M
  });

  // Copy the generated canvas/img into our canvas
  setTimeout(() => {
    const src = tmp.querySelector('canvas') || tmp.querySelector('img');
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, 160, 160);
    if (src && src.tagName === 'CANVAS') {
      ctx.drawImage(src, 6, 6, 148, 148);
    } else if (src) {
      const img = new Image();
      img.onload = () => ctx.drawImage(img, 6, 6, 148, 148);
      img.src = src.src;
    }
    document.body.removeChild(tmp);
  }, 200);
}

function drawFallback() {
  // If CDN fails, show URL text on canvas
  const canvas = document.getElementById('qr-canvas');
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, 160, 160);
  ctx.fillStyle = '#007a8a';
  ctx.font = '11px monospace';
  ctx.textAlign = 'center';
  ctx.fillText('QR unavailable', 80, 75);
  ctx.fillText('(no internet)', 80, 92);
}
</script>
</body>
</html>"""


# ─────────────────────────────────────────────
#  BROWSER PAGE
# ─────────────────────────────────────────────
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

body::before {
  content: '';
  position: fixed;
  inset: 0;
  background: repeating-linear-gradient(
    0deg, transparent, transparent 2px,
    rgba(0,245,255,0.015) 2px, rgba(0,245,255,0.015) 4px
  );
  pointer-events: none;
  z-index: 999;
}

header {
  padding: 14px 20px 12px;
  border-bottom: 1px solid var(--border);
  background: linear-gradient(180deg, rgba(0,245,255,0.05) 0%, transparent 100%);
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.logo {
  font-family: 'Orbitron', sans-serif;
  font-weight: 900;
  font-size: 1.2rem;
  color: var(--cyan);
  text-shadow: 0 0 20px var(--cyan);
  letter-spacing: 4px;
  flex-shrink: 0;
  text-decoration: none;
}

.breadcrumb {
  flex: 1;
  color: var(--muted);
  font-size: 0.75rem;
  word-break: break-all;
  min-width: 0;
}
.breadcrumb a { color: var(--cyan); text-decoration: none; }
.breadcrumb a:hover { color: white; }

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
  font-size: 0.78rem;
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
  background: transparent;
}
.btn-cyan  { color: var(--cyan);    background: rgba(0,245,255,0.07); }
.btn-mag   { color: var(--magenta); background: rgba(255,0,160,0.07); }
.btn-home  { color: var(--yellow);  background: rgba(255,215,0,0.07); }
.btn:hover { filter: brightness(1.4); box-shadow: 0 0 12px currentColor; }

#upload-panel {
  display: none;
  margin: 12px 20px;
  border: 2px dashed var(--cyan-dim);
  border-radius: 8px;
  padding: 24px;
  text-align: center;
  background: rgba(0,245,255,0.03);
  transition: all 0.2s;
}
#upload-panel.visible { display: block; }
#upload-panel.dragover { border-color: var(--cyan); background: rgba(0,245,255,0.08); }
#upload-panel p { color: var(--muted); margin-bottom: 12px; font-size: 0.82rem; }
#file-input { display: none; }
.upload-label {
  cursor: pointer;
  color: var(--cyan);
  border: 1px solid var(--cyan-dim);
  padding: 8px 18px;
  border-radius: 4px;
  font-size: 0.8rem;
  display: inline-block;
  transition: all 0.15s;
}
.upload-label:hover { background: rgba(0,245,255,0.12); }
#upload-progress-wrap { display: none; margin-top: 14px; }
#upload-bar-track { background: var(--border); border-radius: 4px; height: 6px; overflow: hidden; margin-bottom: 6px; }
#upload-bar-fill { height: 100%; width: 0%; background: linear-gradient(90deg, var(--cyan), var(--magenta)); transition: width 0.1s; }
#upload-status { font-size: 0.78rem; color: var(--text); }

.file-list { padding: 12px 20px; }

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
.file-item:hover { border-color: var(--cyan-dim); }
.file-item:hover .file-actions { opacity: 1; }

.file-icon { font-size: 1.2rem; flex-shrink: 0; width: 28px; text-align: center; }
.file-info { flex: 1; min-width: 0; }
.file-name {
  color: var(--text);
  font-size: 0.88rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
  text-decoration: none;
  display: block;
}
.file-name:hover { color: var(--cyan); }
.file-meta { color: var(--muted); font-size: 0.7rem; margin-top: 2px; }

.file-actions {
  display: flex;
  gap: 6px;
  opacity: 0;
  transition: opacity 0.15s;
  flex-shrink: 0;
}
.act-btn {
  font-size: 0.7rem;
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
.act-btn:hover { filter: brightness(1.3); background: rgba(255,255,255,0.05); }

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
  font-size: 0.82rem;
  color: var(--cyan);
  margin-bottom: 14px;
  word-break: break-all;
}
#media-player { width: 100%; border-radius: 6px; background: #000; max-height: 70vh; }

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
  font-size: 0.8rem;
  z-index: 200;
  transition: transform 0.3s;
  white-space: nowrap;
}
#toast.show { transform: translateX(-50%) translateY(0); }

.empty { color: var(--muted); padding: 40px 20px; text-align: center; font-size: 0.85rem; }

.count-tag { color: var(--muted); font-size: 0.75rem; margin-left: auto; }

@media (max-width: 540px) { .file-actions { opacity: 1; } }
</style>
</head>
<body>

<header>
  <a class="logo" href="/">◈ NEXUS</a>
  <div class="breadcrumb">
    <a href="/browse/{{ storage }}/">
      {{ '📱 Internal' if storage == 'internal' else '💾 SD Card' }}
    </a>
    {% set parts = current_path.split('/') %}
    {% set ns = namespace(acc='') %}
    {% for p in parts %}
      {% if p %}
        {% set ns.acc = ns.acc + '/' + p %}
        &nbsp;/&nbsp;<a href="/browse/{{ storage }}/{{ ns.acc.lstrip('/') }}">{{ p }}</a>
      {% endif %}
    {% endfor %}
  </div>
</header>

<div class="toolbar">
  <button class="btn btn-cyan" onclick="toggleUpload()">⬆ Upload</button>
  {% if current_path %}
    <a class="btn btn-mag" href="/browse/{{ storage }}/{{ parent_path }}">⬅ Back</a>
  {% else %}
    <a class="btn btn-mag" href="/">⬅ Home</a>
  {% endif %}
  <span class="count-tag">{{ items|length }} item{{ 's' if items|length != 1 else '' }}</span>
</div>

<div id="upload-panel"
     ondragover="onDrag(event,true)"
     ondragleave="onDrag(event,false)"
     ondrop="onDrop(event)">
  <p>Drop files here or click to select</p>
  <label class="upload-label" for="file-input">Choose files</label>
  <input type="file" id="file-input" multiple onchange="uploadFiles(this.files)">
  <div id="upload-progress-wrap">
    <div id="upload-bar-track"><div id="upload-bar-fill"></div></div>
    <div id="upload-status"></div>
  </div>
</div>

<div class="file-list">
  {% if not items %}
  <div class="empty">▣ Empty directory</div>
  {% endif %}

  {% for item in items %}
  <div class="file-item">
    <div class="file-icon">{{ item.icon }}</div>
    <div class="file-info">
      {% if item.is_dir %}
        <a class="file-name" href="/browse/{{ storage }}/{{ item.path }}">{{ item.name }}/</a>
      {% else %}
        <a class="file-name" href="/file/{{ storage }}/{{ item.path }}" download>{{ item.name }}</a>
      {% endif %}
      <div class="file-meta">
        {% if item.size_h %}{{ item.size_h }}{% endif %}
        {% if item.ext %}&middot; {{ item.ext.upper() }}{% endif %}
      </div>
    </div>
    <div class="file-actions">
      {% if not item.is_dir %}
        <button class="act-btn act-dl" onclick="dlFile('{{ storage }}','{{ item.path }}')">↓ DL</button>
        {% if item.playable %}
        <button class="act-btn act-play"
          onclick="playMedia('{{ storage }}','{{ item.path }}','{{ item.name }}','{{ item.media_type }}')">
          ▶ Play
        </button>
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
    <button class="btn btn-mag" style="margin-top:14px;width:100%" onclick="closeMediaBtn()">✕ Close</button>
  </div>
</div>

<div id="toast"></div>

<script>
const STORAGE = "{{ storage }}";
const CURRENT = "{{ current_path }}";

function toggleUpload() {
  document.getElementById('upload-panel').classList.toggle('visible');
}
function onDrag(e, enter) {
  e.preventDefault();
  document.getElementById('upload-panel').classList.toggle('dragover', enter);
}
function onDrop(e) {
  e.preventDefault(); onDrag(e, false);
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
    xhr.open('POST', '/upload/' + STORAGE + '/' + CURRENT);
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

function dlFile(storage, path) {
  const a = document.createElement('a');
  a.href = '/file/' + storage + '/' + path;
  a.download = '';
  a.click();
}

function playMedia(storage, path, name, type) {
  document.getElementById('media-title').textContent = name;
  const vid = document.getElementById('media-player');
  const aud = document.getElementById('audio-player');
  const url = '/file/' + storage + '/' + path;
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
</html>"""

# ─────────────────────────────────────────────
#  FILE TYPE HELPERS
# ─────────────────────────────────────────────
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

# ─────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────
@app.route("/")
def home():
    ip = get_local_ip()
    share_url = f"http://{ip}:5000"
    return render_template_string(HOME_HTML, share_url=share_url)

@app.route("/browse/<storage>/")
@app.route("/browse/<storage>/<path:req_path>")
def browse(storage, req_path=""):
    if storage not in ROOTS:
        return "Unknown storage", 404
    root = ROOTS[storage]
    abs_path = os.path.join(root, req_path)

    if not os.path.exists(abs_path):
        return "Path not found", 404

    try:
        entries = os.listdir(abs_path)
    except PermissionError:
        return "Permission denied", 403

    raw = []
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
    return render_template_string(
        HTML,
        items=raw,
        current_path=req_path,
        parent_path=parent_path,
        storage=storage
    )

@app.route("/file/<storage>/<path:file_path>")
def get_file(storage, file_path):
    if storage not in ROOTS:
        return "Not found", 404
    full = os.path.join(ROOTS[storage], file_path)
    if not os.path.isfile(full):
        return "File not found", 404
    mime, _ = mimetypes.guess_type(full)
    return send_file(full, mimetype=mime or 'application/octet-stream',
                     as_attachment=request.args.get('dl') == '1')

@app.route("/upload/<storage>/", methods=["POST"])
@app.route("/upload/<storage>/<path:req_path>", methods=["POST"])
def upload(storage, req_path=""):
    if storage not in ROOTS:
        return jsonify({"error": "Unknown storage"}), 400
    dest_dir = os.path.join(ROOTS[storage], req_path)
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
    ip = get_local_ip()
    print(f"\n  ◈ NEXUS/FS running at http://{ip}:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
