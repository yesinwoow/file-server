from flask import Flask, render_template, send_from_directory, request
import os

app = Flask(__name__)

VIDEO_PATH = "/storage/3CBE-B049/VIDEO💿💿/Song"
THUMB_PATH = VIDEO_PATH

def get_videos():
    data = {}
    for root, dirs, files in os.walk(VIDEO_PATH):
        category = os.path.basename(root)
        vids = [f for f in files if f.lower().endswith((".mp4", ".mkv", ".avi"))]
        if vids:
            data[category] = vids
    return data

@app.route('/')
def index():
    search = request.args.get('search', '').lower()
    categories = get_videos()

    if search:
        categories = {
            cat: [v for v in vids if search in v.lower()]
            for cat, vids in categories.items()
        }

    return render_template('index.html', categories=categories, search=search)

@app.route('/video/<path:filename>')
def video(filename):
    return send_from_directory(VIDEO_PATH, filename)

@app.route('/thumb/<path:filename>')
def thumb(filename):
    return send_from_directory(THUMB_PATH, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)