import base64
import json
import os
import threading
import time
from pathlib import Path

import requests
from flask import Flask, jsonify, render_template, request

BASE = Path(__file__).parent
DATA_FILE = BASE / "data.json"
LOCK = threading.Lock()
DIRTY = threading.Event()

app = Flask(__name__)


def load_data():
    with DATA_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    tmp = DATA_FILE.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(DATA_FILE)


def push_via_api():
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("REPO")
    branch = os.environ.get("GIT_BRANCH", "main")
    if not token or not repo:
        print("[commit-worker] GITHUB_TOKEN/REPO not set — skipping push", flush=True)
        return

    with LOCK:
        data = load_data()

    content_b64 = base64.b64encode(
        json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
    ).decode()

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    url = f"https://api.github.com/repos/{repo}/contents/data.json"

    r = requests.get(url, headers=headers, params={"ref": branch}, timeout=20)
    sha = r.json().get("sha") if r.ok else None

    payload = {
        "message": "chore(data): update likes [skip ci]",
        "content": content_b64,
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(url, headers=headers, json=payload, timeout=20)
    print(f"[commit-worker] push status={r.status_code}", flush=True)


def commit_worker():
    # Debounced background pusher — pushes data.json to repo on every like
    while True:
        if DIRTY.wait(timeout=30):
            DIRTY.clear()
            time.sleep(1.0)
            try:
                push_via_api()
            except Exception as e:  # noqa: BLE001
                print(f"[commit-worker] error: {e}", flush=True)


@app.route("/")
def index():
    d = load_data()
    return render_template(
        "index.html",
        title=d.get("title", "IRIS"),
        created_by=d.get("created_by", "MUHAMMAD TAQI"),
        icon=d.get("icon", ""),
    )


@app.route("/api/data")
def api_data():
    with LOCK:
        d = load_data()
    items = sorted(d["items"], key=lambda x: x.get("likes", 0), reverse=True)
    return jsonify(
        title=d.get("title", "IRIS"),
        created_by=d.get("created_by", "MUHAMMAD TAQI"),
        icon=d.get("icon", ""),
        items=items,
        total_likes=sum(i.get("likes", 0) for i in d["items"]),
    )


@app.route("/api/like", methods=["POST"])
def api_like():
    body = request.get_json(silent=True) or {}
    item_id = body.get("id")
    if not item_id:
        return jsonify(ok=False, error="missing id"), 400

    with LOCK:
        d = load_data()
        found = None
        for it in d["items"]:
            if it["id"] == item_id:
                it["likes"] = int(it.get("likes", 0)) + 1
                found = it["likes"]
                break
        if found is None:
            return jsonify(ok=False, error="not found"), 404
        save_data(d)

    DIRTY.set()
    return jsonify(ok=True, likes=found)


if __name__ == "__main__":
    threading.Thread(target=commit_worker, daemon=True).start()
    print("IRIS running on http://127.0.0.1:5000", flush=True)
    app.run(host="127.0.0.1", port=5000, threaded=True)
