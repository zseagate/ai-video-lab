#!/usr/bin/env python3
"""Submit the Sichuan keyframe prompts to a local ComfyUI server.

Usage:
  python comfyui_keyframes.py --server http://127.0.0.1:8188 ^
      --prompts ..\05_prompts --out ..\assets\keyframes ^
      --checkpoint v1-5-pruned-emaonly.safetensors --width 768 --height 432
"""
from __future__ import annotations

import argparse
import json
import re
import time
import uuid
from pathlib import Path

import requests


def extract_image_prompt(text: str) -> tuple[str, str]:
    positive = text
    if "IMAGE PROMPT" in positive:
        positive = positive.split("IMAGE PROMPT", 1)[1]
    for stop in ("VIDEO MOTION PROMPT", "NEGATIVE"):
        if stop in positive:
            positive = positive.split(stop, 1)[0]
    negative = ""
    if "NEGATIVE" in text:
        negative = text.split("NEGATIVE", 1)[1]
    return " ".join(positive.split()), " ".join(negative.split())


def workflow(prompt: str, negative: str, checkpoint: str, width: int, height: int, seed: int, prefix: str):
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": checkpoint}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["1", 1]}},
        "4": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0],
            },
        },
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": prefix}},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--checkpoint", default="v1-5-pruned-emaonly.safetensors")
    ap.add_argument("--width", type=int, default=768)
    ap.add_argument("--height", type=int, default=432)
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--only", default="")
    args = ap.parse_args()

    prompts_dir = Path(args.prompts)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    client_id = str(uuid.uuid4())

    files = sorted(prompts_dir.glob("S*.txt"))
    if args.only:
        wanted = {x.strip().upper() for x in args.only.split(",")}
        files = [p for p in files if p.stem.upper() in wanted]

    for path in files:
        text = path.read_text(encoding="utf-8")
        positive, negative = extract_image_prompt(text)
        nums = re.findall(r"\d+", path.stem[1:])
        seed = 20261022 + (int(nums[0]) if nums else 0) * 17
        wf = workflow(positive, negative, args.checkpoint, args.width, args.height, seed, f"sichuan_{path.stem}")
        wf["5"]["inputs"]["steps"] = args.steps

        print(f"\n=== {path.stem} ===")
        print("positive:", positive[:160], "...")
        r = requests.post(f"{args.server}/prompt", json={"prompt": wf, "client_id": client_id}, timeout=30)
        if r.status_code != 200:
            print("submit failed:", r.status_code, r.text)
            return 1
        prompt_id = r.json()["prompt_id"]
        print("prompt_id:", prompt_id)

        deadline = time.time() + 60 * 30
        while time.time() < deadline:
            h = requests.get(f"{args.server}/history/{prompt_id}", timeout=30).json()
            if prompt_id in h:
                outputs = h[prompt_id].get("outputs", {})
                images = outputs.get("7", {}).get("images", [])
                if images:
                    for img in images:
                        src = Path(img.get("filename", ""))
                        print("output:", src)
                        # ComfyUI writes to its own output dir; caller can copy by filename.
                print("done:", path.stem)
                break
            time.sleep(3)
        else:
            print("timeout:", path.stem)
            return 2

    print("\nAll submitted. Copy ComfyUI/output/sichuan_S*.png to assets/keyframes/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
