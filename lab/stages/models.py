"""Local model registry and downloader (offline-first).

Small GGUF instruct models for CPU prompt enhancement. Nothing here runs at
import time; downloads only happen when explicitly requested. ModelScope is the
default host because it is reachable from mainland networks.

Usage (CLI):
  python lab/run.py models --list
  python lab/run.py models --download qwen2.5-0.5b-instruct-q4
"""
from __future__ import annotations

import os
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = ROOT_DIR / "models"

# Curated CPU-friendly models. `size` is the expected byte size (best effort).
REGISTRY: dict[str, dict] = {
    "qwen2.5-0.5b-instruct-q4": {
        "file": "qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "url": (
            "https://modelscope.cn/models/Qwen/Qwen2.5-0.5B-Instruct-GGUF/"
            "resolve/master/qwen2.5-0.5b-instruct-q4_k_m.gguf"
        ),
        "size": 491_400_032,
        "params": "0.5B",
        "note": "fastest; ~470MB; good for short prompt rewrites",
    },
    "qwen2.5-1.5b-instruct-q4": {
        "file": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "url": (
            "https://modelscope.cn/models/Qwen/Qwen2.5-1.5B-Instruct-GGUF/"
            "resolve/master/qwen2.5-1.5b-instruct-q4_k_m.gguf"
        ),
        "size": 1_015_000_000,
        "params": "1.5B",
        "note": "better quality; ~1GB; still CPU-usable",
    },
}

# Preferred order when no explicit model is requested.
PREFERENCE = ["qwen2.5-1.5b-instruct-q4", "qwen2.5-0.5b-instruct-q4"]


def path(name: str) -> Path:
    """Absolute path where a registry model is stored."""
    if name not in REGISTRY:
        raise KeyError(f"unknown model: {name}")
    return MODELS_DIR / REGISTRY[name]["file"]


def installed(name: str) -> bool:
    p = path(name)
    if not p.exists() or p.stat().st_size < 1024:
        return False
    return _is_gguf(p)


def _is_gguf(p: Path) -> bool:
    try:
        with p.open("rb") as f:
            return f.read(4) == b"GGUF"
    except OSError:
        return False


def status() -> list[dict]:
    out = []
    for name, meta in REGISTRY.items():
        p = path(name)
        size = p.stat().st_size if p.exists() else 0
        out.append(
            {
                "name": name,
                "file": meta["file"],
                "params": meta.get("params", ""),
                "note": meta.get("note", ""),
                "installed": installed(name),
                "size": size,
                "size_mb": round(size / 1_048_576, 1),
                "expected_mb": round(meta.get("size", 0) / 1_048_576, 1),
                "path": str(p),
            }
        )
    return out


def resolve_default() -> str | None:
    """Return the best installed model name, or None."""
    for name in PREFERENCE:
        if installed(name):
            return name
    return None


def download(name: str, overwrite: bool = False) -> dict:
    """Download a registry model with a simple progress callback. Returns a dict."""
    if name not in REGISTRY:
        return {"status": "error", "reason": f"unknown model: {name}"}
    target = path(name)
    if installed(name) and not overwrite:
        return {"status": "ok", "model": name, "path": str(target), "skipped": True}

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".part")
    req = urllib.request.Request(
        REGISTRY[name]["url"],
        headers={"User-Agent": "ai-video-lab/0.1 (+local model downloader)"},
    )
    written = 0
    try:
        with urllib.request.urlopen(req, timeout=60) as resp, tmp.open("wb") as fh:
            while True:
                chunk = resp.read(1 << 20)
                if not chunk:
                    break
                fh.write(chunk)
                written += len(chunk)
                if written % (64 << 20) < (1 << 20):
                    print(f"  {name}: {written / 1_048_576:.0f} MB", flush=True)
        if written < 1024 or not _is_gguf(tmp):
            tmp.unlink(missing_ok=True)
            return {"status": "error", "reason": "download is not a GGUF file", "model": name}
        os.replace(tmp, target)
        return {"status": "ok", "model": name, "path": str(target), "bytes": written}
    except Exception as e:
        tmp.unlink(missing_ok=True)
        return {"status": "error", "reason": str(e), "model": name}
