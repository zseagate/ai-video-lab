"""Local Wan video engine adapter (pluggable).

Detects the ComfyUI + Wan 2.1 T2V 1.3B install and renders short 480p draft clips
via the ComfyUI HTTP API. Falls back gracefully (returns ready=False) so the
assembly chain never breaks on machines without the models.

NOTE: on a CPU-only machine this is slow (a 9-frame / 10-step draft can take
minutes). Keep frames/steps low for drafting; full 5s shots belong on a GPU box
or a cloud engine.
"""
from __future__ import annotations

import json
import subprocess
import time
import urllib.request
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parent
REPO = LAB_DIR.parent
COMFY = REPO / "ComfyUI"
DEFAULT_PORT = 8188

MODELS = {
    "unet": "diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors",
    "clip": "text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors",
    "vae": "vae/wan_2.1_vae.safetensors",
}


def find_comfy() -> Path | None:
    return COMFY if (COMFY / "main.py").exists() else None


def models_ready() -> bool:
    if not find_comfy():
        return False
    for rel in MODELS.values():
        if not (COMFY / "models" / rel).exists():
            return False
    return True


def server_running(port: int = DEFAULT_PORT) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/system_stats", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def start_server(port: int = DEFAULT_PORT) -> subprocess.Popen | None:
    """Start ComfyUI headless on CPU in the background. Returns the process or None."""
    if not find_comfy():
        return None
    py = None
    for cand in [REPO / "env" / "comfy" / "Scripts" / "python.exe", "python"]:
        try:
            subprocess.run([str(cand), "--version"], capture_output=True, timeout=15)
            py = str(cand)
            break
        except Exception:
            continue
    if not py:
        return None
    log = LAB_DIR / "projects" / ".comfy_server.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8") as f:
        proc = subprocess.Popen(
            [py, str(COMFY / "main.py"), "--cpu", "--listen", "127.0.0.1", "--port", str(port)],
            stdout=f, stderr=subprocess.STDOUT, cwd=str(COMFY),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    # Wait for readiness.
    for _ in range(60):
        if server_running(port):
            return proc
        time.sleep(2)
    return proc


def build_prompt(prompt_text: str, width: int = 832, height: int = 480,
                 frames: int = 9, steps: int = 10, seed: int = 1) -> dict:
    """Build a ComfyUI API-format prompt for Wan 2.1 T2V 1.3B."""
    neg = "text, watermark, subtitle, blurry, deformed, low quality"
    return {
        "37": {"class_type": "UNETLoader",
               "inputs": {"unet_name": MODELS["unet"].split("/", 1)[1], "weight_dtype": "default"}},
        "38": {"class_type": "CLIPLoader",
               "inputs": {"clip_name": MODELS["clip"].split("/", 1)[1], "type": "wan", "device": "default"}},
        "39": {"class_type": "VAELoader", "inputs": {"vae_name": MODELS["vae"].split("/", 1)[1]}},
        "40": {"class_type": "EmptyHunyuanLatentVideo",
               "inputs": {"width": width, "height": height, "length": frames, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt_text, "clip": ["38", 0]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["38", 0]}},
        "3": {"class_type": "KSampler", "inputs": {
            "model": ["37", 0], "seed": seed, "steps": steps, "cfg": 5.0,
            "sampler_name": "uni_pc", "scheduler": "simple",
            "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["40", 0], "denoise": 1.0}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["39", 0]}},
        "47": {"class_type": "SaveWEBM", "inputs": {
            "images": ["8", 0], "filename_prefix": "wan_draft", "codec": "vp9", "fps": 16.0, "crf": 32.0}},
    }


def _post(url: str, data: dict) -> dict:
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def render(prompt_text: str, out_webm: Path, port: int = DEFAULT_PORT,
           width: int = 832, height: int = 480, frames: int = 9,
           steps: int = 10, seed: int = 1, timeout_s: int = 1800) -> dict:
    """Render one draft clip via the running ComfyUI server. Returns result dict."""
    if not server_running(port):
        return {"status": "error", "reason": "comfy server not running"}
    prompt = build_prompt(prompt_text, width, height, frames, steps, seed)
    resp = _post(f"http://127.0.0.1:{port}/prompt",
                 {"prompt": prompt, "client_id": "lab-wan"})
    pid = resp.get("prompt_id")
    if not pid:
        return {"status": "error", "reason": "no prompt_id", "resp": resp}

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        time.sleep(10)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/history/{pid}", timeout=30) as r:
                hist = json.loads(r.read().decode("utf-8"))
        except Exception:
            continue
        entry = hist.get(pid)
        if not entry:
            continue
        if entry.get("status", {}).get("completed"):
            outputs = entry.get("outputs", {})
            img = None
            for node in outputs.values():
                for key in ("images", "gifs"):
                    for it in node.get(key, []):
                        if it.get("type") == "output":
                            img = it
            if img:
                src = COMFY / "output" / img.get("subfolder", "") / img["filename"]
                if src.exists():
                    out_webm.parent.mkdir(parents=True, exist_ok=True)
                    out_webm.write_bytes(src.read_bytes())
                    return {"status": "ok", "source": str(src), "out": str(out_webm)}
            return {"status": "ok", "reason": "completed but no output file", "outputs": outputs}
        if entry.get("status", {}).get("status_str") == "error":
            return {"status": "error", "reason": "comfy execution error", "outputs": outputs}
    return {"status": "error", "reason": "timeout"}


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", default="a red lantern swaying in the rain at night, cinematic")
    ap.add_argument("--out", default=str(LAB_DIR / "projects" / "wan_draft.webm"))
    ap.add_argument("--frames", type=int, default=9)
    ap.add_argument("--steps", type=int, default=10)
    args = ap.parse_args()
    print("comfy:", find_comfy())
    print("models_ready:", models_ready())
    print("server_running:", server_running())
    print(json.dumps(render(args.prompt, Path(args.out), frames=args.frames, steps=args.steps),
                     ensure_ascii=False))
