"""Local small-LLM prompt enhancement (optional, CPU-only, offline).

Uses llama-cpp-python with a small GGUF instruct model to rewrite a Seedance
prompt, then re-normalises the result through the rules engine so the 10-layer
structure and cross-shot consistency anchors are always preserved.

Graceful degradation: if llama-cpp-python or a model is missing, `enhance()`
falls back to the rules-based `promptgen.optimize()` and reports
`engine: rules`. Nothing here downloads a model or touches the network.

Model choice (first hit wins):
  1. LAB_LLM_MODEL env var: a registry name OR a path to a .gguf file
  2. the best installed model in stages.models (1.5B preferred over 0.5B)
"""
from __future__ import annotations

import os
import threading
from pathlib import Path

_LOCK = threading.Lock()
_LLM = None
_LLM_KEY: str | None = None


def _registry():
    try:
        from stages import models  # type: ignore

        return models
    except Exception:
        import models  # type: ignore

        return models


def _resolve_model() -> Path | None:
    raw = os.environ.get("LAB_LLM_MODEL", "").strip()
    reg = _registry()
    if raw:
        p = Path(raw)
        if p.exists():
            return p
        try:
            rp = reg.path(raw)
            if rp.exists():
                return rp
        except KeyError:
            pass
    name = reg.resolve_default()
    if name:
        return reg.path(name)
    return None


def _get_llm():
    """Lazily load and cache the Llama instance (thread-safe)."""
    global _LLM, _LLM_KEY
    model_path = _resolve_model()
    if model_path is None:
        return None
    key = str(model_path)
    with _LOCK:
        if _LLM is not None and _LLM_KEY == key:
            return _LLM
        try:
            from llama_cpp import Llama  # type: ignore
        except Exception:
            return None
        cpu = os.cpu_count() or 4
        threads = max(2, min(4, cpu // 2 or 2))
        _LLM = Llama(
            model_path=key,
            n_ctx=2048,
            n_threads=threads,
            n_batch=128,
            verbose=False,
        )
        _LLM_KEY = key
        return _LLM


def status() -> dict:
    reg = _registry()
    model = _resolve_model()
    try:
        import llama_cpp  # type: ignore

        lib = getattr(llama_cpp, "__version__", "unknown")
    except Exception:
        lib = None
    return {
        "available": bool(lib and model),
        "llama_cpp": lib,
        "model": str(model) if model else None,
        "model_name": model.name if model else None,
        "default_registry_model": reg.resolve_default(),
    }


def reset() -> None:
    """Unload the cached model (frees RAM)."""
    global _LLM, _LLM_KEY
    with _LOCK:
        _LLM = None
        _LLM_KEY = None


def _rules(text: str, shot: dict | None, style: dict | None) -> dict:
    try:
        from stages import promptgen  # type: ignore
    except Exception:
        import promptgen  # type: ignore

    res = promptgen.optimize(text, shot, style)
    res["engine"] = "rules"
    return res


_SYSTEM = (
    "You are a cinematography prompt editor. Rewrite the user's shot prompt into "
    "clear, concrete English that a text-to-video model can follow. Keep every "
    "named character, costume, prop and colour tone unchanged. Keep these labelled "
    "lines: subject, action, character, environment, lighting, camera, style, "
    "consistent, format, negative. Do not invent new people or plots. Output ONLY "
    "the labelled prompt lines, no explanation."
)


def enhance(text: str, shot: dict | None = None, style: dict | None = None) -> dict:
    """Enhance a prompt with the local LLM, then normalise with the rules engine."""
    orig = (text or "").strip()
    if not orig:
        return {"ok": False, "error": "empty prompt", "engine": "rules"}

    llm = _get_llm()
    if llm is None:
        return _rules(orig, shot, style)

    try:
        out = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": orig},
            ],
            temperature=0.4,
            max_tokens=420,
            top_p=0.9,
        )
        raw = (out["choices"][0]["message"]["content"] or "").strip()
    except Exception as e:
        res = _rules(orig, shot, style)
        res["llm_error"] = str(e)
        return res

    if not raw:
        return _rules(orig, shot, style)

    # Normalise the LLM output: fill missing layers, dedup, re-sync anchors.
    res = _rules(raw, shot, style)
    if not res.get("ok"):
        return _rules(orig, shot, style)
    res["engine"] = "llm"
    res["llm_model"] = Path(_LLM_KEY).name if _LLM_KEY else None
    res["changed"] = ["llm rewrite"] + list(res.get("changed", []))
    return res
