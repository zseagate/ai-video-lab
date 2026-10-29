"""Cloud Seedance engine adapter (pluggable, optional).

Renders a shot by submitting a Seedance (Volcano Ark) task, polling until done,
then downloading the result mp4. Pure stdlib (urllib) so the lab needs no extra deps.

The model is closed-source; this is the cloud integration layer referenced in
lab/README.md ("云端引擎"). Requires ARK_API_KEY + ARK_MODEL_ID (and, for I2V,
a first-frame image). Always degrade gracefully: is_ready() returns False when
credentials are missing so composite falls back to placeholders.
"""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.request
from pathlib import Path

DEFAULT_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks"


def is_ready() -> bool:
    return bool(os.environ.get("ARK_API_KEY") and os.environ.get("ARK_MODEL_ID"))


def _image_data_url(image: Path) -> str:
    suffix = image.suffix.lower().lstrip(".") or "png"
    mime = "image/jpeg" if suffix in ("jpg", "jpeg") else "image/png"
    data = base64.b64encode(image.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def _http_json(url: str, data: dict | None = None, headers: dict | None = None, timeout: int = 120) -> dict:
    req = urllib.request.Request(url, data=(json.dumps(data).encode("utf-8") if data is not None else None),
                                 headers=headers or {}, method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def submit(prompt_text: str, image: Path | None, duration: int = 5, ratio: str = "16:9") -> dict:
    """Submit one Seedance generation task. Returns the task response dict."""
    key = os.environ.get("ARK_API_KEY")
    model = os.environ.get("ARK_MODEL_ID")
    endpoint = os.environ.get("ARK_ENDPOINT", DEFAULT_ENDPOINT)
    if not key or not model:
        raise RuntimeError("ARK_API_KEY and ARK_MODEL_ID are required for cloud Seedance")
    content: list[dict] = [{"type": "text", "text": prompt_text}]
    if image and image.exists():
        content.append({"type": "image_url", "image_url": {"url": _image_data_url(image)}})
    payload = {"model": model, "content": content, "duration": duration,
               "ratio": ratio, "watermark": False}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    return _http_json(endpoint, payload, headers)


def poll(task_id: str, timeout_s: int = 900, interval: int = 10) -> dict:
    """Poll a task until succeeded/failed. Returns the final task dict."""
    key = os.environ.get("ARK_API_KEY")
    endpoint = os.environ.get("ARK_ENDPOINT", DEFAULT_ENDPOINT)
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            task = _http_json(f"{endpoint}/{task_id}", headers=headers, timeout=60)
        except Exception:
            task = {}
        status = str(task.get("status", "")).lower()
        if status in ("succeeded", "success", "done"):
            return task
        if status in ("failed", "error", "cancelled", "canceled"):
            return task
        time.sleep(interval)
    return {"status": "timeout", "task_id": task_id}


def _extract_video_url(task: dict) -> str | None:
    content = task.get("content") or task.get("result") or {}
    if isinstance(content, dict):
        return content.get("video_url") or content.get("url")
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                v = item.get("video_url") or item.get("url")
                if v:
                    return v
    return None


def render(prompt_text: str, out_mp4: Path, image: Path | None = None,
           duration: int = 5, ratio: str = "16:9", timeout_s: int = 900) -> dict:
    """Submit + poll + download. Returns result dict with local mp4 path on success."""
    if not is_ready():
        return {"status": "error", "reason": "ARK_API_KEY / ARK_MODEL_ID not set"}
    try:
        task = submit(prompt_text, image, duration, ratio)
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "reason": f"submit failed: {e}"}
    task_id = task.get("id") or task.get("task_id")
    if not task_id:
        return {"status": "error", "reason": "no task id in response", "resp": task}
    task = poll(task_id, timeout_s)
    status = str(task.get("status", "")).lower()
    if status in ("failed", "error", "timeout"):
        return {"status": "error", "reason": f"task {status}", "task": task}
    url = _extract_video_url(task)
    if not url:
        return {"status": "error", "reason": "no video url in task result", "task": task}
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=120) as r, open(out_mp4, "wb") as f:
            f.write(r.read())
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "reason": f"download failed: {e}", "task": task}
    return {"status": "ok", "task_id": task_id, "out": str(out_mp4)}


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", default="slow push-in, rain falling, lantern glow")
    ap.add_argument("--image", default=None)
    ap.add_argument("--out", default="lab/projects/seedance_draft.mp4")
    ap.add_argument("--duration", type=int, default=5)
    args = ap.parse_args()
    print("ready:", is_ready())
    print(json.dumps(render(args.prompt, Path(args.out),
                            Path(args.image) if args.image else None, args.duration),
                     ensure_ascii=False, indent=2))
