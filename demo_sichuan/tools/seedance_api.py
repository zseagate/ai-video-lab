#!/usr/bin/env python3
"""Seedance / Volcano Ark image-to-video placeholder.

This script is intentionally safe by default: it prints the request and exits
unless --execute is passed AND ARK_API_KEY / ARK_MODEL_ID are set.

Docs: https://www.volcengine.com/docs/82379
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

ENV_HELP = """
Seedance environment check
=========================
ARK_API_KEY  : %s
ARK_MODEL_ID : %s

Rules:
- ARK_API_KEY must be the plain-text API Key from the Ark console.
- ARK_MODEL_ID should be a Seedance model ID, not an endpoint ID.
- If ARK_MODEL_ID starts with 'ep-', this is usually an endpoint ID, not a model ID.

If you are only checking the environment, run:
  python seedance_api.py --check-env

To do a dry run:
  python seedance_api.py --prompt-file <file> --image <png> --out <json>

To actually call Seedance:
  python seedance_api.py --prompt-file <file> --image <png> --out <json> --execute
""".strip()


def read_prompt(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    marker = "VIDEO MOTION PROMPT"
    if marker in text:
        text = text.split(marker, 1)[1]
        # stop at the next section header
        for stop in ("NEGATIVE", "IMAGE PROMPT"):
            if stop in text:
                text = text.split(stop, 1)[0]
    return " ".join(text.split())


def image_to_data_url(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".") or "png"
    mime = "image/jpeg" if suffix in ("jpg", "jpeg") else "image/png"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def check_env() -> int:
    key = os.environ.get("ARK_API_KEY")
    model = os.environ.get("ARK_MODEL_ID")
    print(ENV_HELP % ("set" if key else "missing", "set" if model else "missing"))
    if model and model.startswith("ep-"):
        print("\nWARNING: ARK_MODEL_ID looks like an endpoint ID (ep-...).")
        print("Seedance task creation usually needs a model ID, not an endpoint ID.")
        return 3
    if model and "seedance" not in model.lower():
        print("\nWARNING: ARK_MODEL_ID does not look like a Seedance model ID.")
        print("Use a Seedance model ID from the Ark console, not another model or endpoint ID.")
        return 3
    if not key or not model:
        print("\nMissing ARK_API_KEY or ARK_MODEL_ID. Set both environment variables before --execute.")
        return 2
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1]
    ap.add_argument("--prompt-file", default=str(project_root / "demo_sichuan" / "05_prompts" / "S01_test.txt"))
    ap.add_argument("--image", default=str(project_root / "demo_sichuan" / "assets" / "keyframes" / "S01_test.png"))
    ap.add_argument("--out", default=str(project_root / "demo_sichuan" / "assets" / "seedance" / "S01_test.json"))
    ap.add_argument("--duration", type=int, default=5)
    ap.add_argument("--ratio", default="16:9")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--check-env", action="store_true", help="only check ARK_API_KEY / ARK_MODEL_ID")
    args = ap.parse_args()

    if args.check_env:
        return check_env()

    prompt_path = Path(args.prompt_file)
    image_path = Path(args.image)
    out_path = Path(args.out)
    prompt = read_prompt(prompt_path) if prompt_path.exists() else "slow push-in, rain falling, lantern glow"
    if not image_path.exists():
        print(f"missing image: {image_path}", file=sys.stderr)
        return 2

    payload = {
        "model": os.environ.get("ARK_MODEL_ID", "YOUR_SEEDANCE_MODEL_ID"),
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_to_data_url(image_path)}},
        ],
        "duration": args.duration,
        "ratio": args.ratio,
        "watermark": False,
    }

    print("=== Seedance request (dry run) ===")
    preview = json.loads(json.dumps(payload))
    preview["content"][1]["image_url"]["url"] = "<base64 image>"
    print(json.dumps(preview, ensure_ascii=False, indent=2))

    if not args.execute:
        print("\nDry run only. Add --execute and set ARK_API_KEY / ARK_MODEL_ID to call the API.")
        return 0

    key = os.environ.get("ARK_API_KEY")
    model = os.environ.get("ARK_MODEL_ID")
    if not key or not model:
        print("ARK_API_KEY and ARK_MODEL_ID are required for --execute", file=sys.stderr)
        return 2
    if requests is None:
        print("requests is not installed; run: pip install requests", file=sys.stderr)
        return 2

    endpoint = os.environ.get(
        "ARK_ENDPOINT",
        "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks",
    )
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    r = requests.post(endpoint, headers=headers, json=payload, timeout=120)
    print("status:", r.status_code)
    print(r.text)
    r.raise_for_status()

    task = r.json()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved task response: {out_path}")
    print("Next: poll the task ID in the Ark console, then download the mp4.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
