"""Local environment discovery (offline only).

Central place to find external tools and report readiness. No network calls
are made here, so `run.py doctor` works on a fully offline machine.

Resolution order for ffmpeg:
  1. FFMPEG_BIN environment variable (explicit override)
  2. project-local bin/ffmpeg[.exe]
  3. ffmpeg on PATH
  4. common CapCut install locations (Windows)
  5. imageio-ffmpeg bundled binary
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = LAB_DIR.parent

FFMPEG_ENV = "FFMPEG_BIN"
SETTINGS_FILE = LAB_DIR / "low_spec.json"

LOW_SPEC_DEFAULTS = {
    "enabled": False,
    "engine": "",          # empty -> kenburns when low_spec, else wan_local
    "width": 854,
    "height": 480,
    "fps": 16,
}


def load_settings() -> dict:
    """Load low-spec settings (never fails; returns defaults if absent)."""
    import json

    data = dict(LOW_SPEC_DEFAULTS)
    try:
        if SETTINGS_FILE.exists():
            disk = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if isinstance(disk, dict):
                data.update({k: disk[k] for k in LOW_SPEC_DEFAULTS if k in disk})
    except Exception:
        pass
    return data


def save_settings(update: dict) -> dict:
    """Merge and persist low-spec settings. Returns the merged result."""
    import json

    data = load_settings()
    for k in LOW_SPEC_DEFAULTS:
        if k in update:
            data[k] = update[k]
    try:
        SETTINGS_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError:
        pass
    return data


def composite_defaults() -> dict:
    """Resolve composite defaults from low-spec settings.

    Low-spec mode favours the zero-inference keyframe engine at 480p/16fps so a
    4-core CPU can preview an edit without touching a video model.
    """
    s = load_settings()
    low = bool(s.get("enabled"))
    engine = s.get("engine") or ("kenburns" if low else "wan_local")
    return {
        "engine": engine,
        "width": int(s.get("width", 854)) if low else 1280,
        "height": int(s.get("height", 480)) if low else 720,
        "fps": int(s.get("fps", 16)) if low else 30,
        "low_spec": low,
    }


def ffmpeg_candidates() -> list[Path]:
    """Return candidate ffmpeg paths in priority order (may include missing)."""
    out: list[Path] = []

    env = os.environ.get(FFMPEG_ENV)
    if env:
        out.append(Path(env))

    for name in ("ffmpeg.exe", "ffmpeg"):
        out.append(ROOT_DIR / "bin" / name)

    which = shutil.which("ffmpeg")
    if which:
        out.append(Path(which))

    out.extend(
        [
            Path(r"D:\Program Files\CapCut\ffmpeg.exe"),
            Path(r"C:\Program Files\CapCut\ffmpeg.exe"),
            Path(r"D:\Program Files\CapCut Drafts\..\CapCut\ffmpeg.exe"),
        ]
    )

    try:
        import imageio_ffmpeg  # type: ignore

        out.append(Path(imageio_ffmpeg.get_ffmpeg_exe()))
    except Exception:
        pass

    return out


def find_ffmpeg() -> str | None:
    """Return the first existing ffmpeg binary, or None."""
    for cand in ffmpeg_candidates():
        try:
            if cand and cand.exists():
                return str(cand)
        except OSError:
            continue
    return None


def ffmpeg_version(ffmpeg: str | None) -> str | None:
    """Return the first line of `ffmpeg -version`, or None."""
    if not ffmpeg:
        return None
    try:
        r = subprocess.run(
            [ffmpeg, "-version"], capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0 and r.stdout:
            return r.stdout.splitlines()[0].strip()
    except Exception:
        pass
    return None


def _llama_cpp_version() -> str | None:
    try:
        import llama_cpp  # type: ignore

        return getattr(llama_cpp, "__version__", "unknown")
    except Exception:
        return None


def _gguf_models() -> list[str]:
    """List .gguf files under models/ (name only)."""
    mdir = ROOT_DIR / "models"
    if not mdir.exists():
        return []
    try:
        return sorted(f.name for f in mdir.rglob("*.gguf") if f.is_file())
    except OSError:
        return []


def engine_readiness() -> dict:
    """Report which composite engines are usable right now (offline checks)."""
    ready: dict[str, bool | str] = {}

    # footage: any project asset present (checked per project at runtime).
    ready["footage"] = "needs project/assets/footage/<shot>.mp4"
    ready["placeholder"] = True
    ready["kenburns"] = "needs project/assets/keyframes/<shot>.png (or gradient card)"

    # cloud Seedance: credentials present?
    try:
        from stages import seedance  # type: ignore

        ready["seedance"] = bool(seedance.is_ready())
    except Exception:
        ready["seedance"] = False

    # local Wan: models + server.
    try:
        import wan  # type: ignore

        ready["wan_local"] = bool(wan.models_ready() and wan.server_running())
    except Exception:
        ready["wan_local"] = False

    return ready


def doctor() -> dict:
    """Collect a human-readable readiness report. No network access."""
    ffmpeg = find_ffmpeg()
    report = {
        "python": sys.version.split()[0],
        "python_exe": sys.executable,
        "platform": sys.platform,
        "root": str(ROOT_DIR),
        "ffmpeg": ffmpeg,
        "ffmpeg_version": ffmpeg_version(ffmpeg),
        "ffmpeg_env": os.environ.get(FFMPEG_ENV),
        "llama_cpp": _llama_cpp_version(),
        "gguf_models": _gguf_models(),
        "models_dir": str(ROOT_DIR / "models"),
        "engines": engine_readiness(),
    }
    return report
