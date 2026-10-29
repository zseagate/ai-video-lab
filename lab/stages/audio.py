"""Stage 4: sound. Placeholder voice (Windows SAPI) per shot; swap in Suno later.

Each shot gets `audio/voice/<shot>.wav`. If SAPI is unavailable or the text
is empty, a short silence WAV is generated so the assembly chain never breaks.
"""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path


def _silence_wav(path: Path, seconds: float = 1.0, rate: int = 16000) -> None:
    """Write a short silence WAV (no third-party deps)."""
    frames = int(seconds * rate)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * frames)


def _sapi_speak(text: str, out_wav: Path, rate: int = 1) -> bool:
    """Speak text into a WAV using Windows PowerShell System.Speech. Returns success.

    The text is embedded directly in the command (single quotes escaped), which is
    reliable on Windows where stdin piping and temp-file IO are fragile.
    """
    safe = text.replace("'", "''")
    ps = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f"$s.Rate = {int((rate - 1) * 10)}; "
        f"$s.SetOutputToWaveFile('{out_wav}'); "
        f"$s.Speak('{safe}'); $s.Dispose()"
    )
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            capture_output=True,
            timeout=60,
        )
        return proc.returncode == 0 and out_wav.exists() and out_wav.stat().st_size > 44
    except Exception:
        return False


def run(project: Path, rate: int = 1) -> dict:
    project = Path(project)
    shot_list = project / "shot_list.csv"
    if not shot_list.exists():
        raise FileNotFoundError("shot_list.csv not found; run storyboard first")

    voice_dir = project / "audio" / "voice"
    voice_dir.mkdir(parents=True, exist_ok=True)

    rows = list(csv.DictReader(shot_list.open(encoding="utf-8-sig")))
    generated = []
    for row in rows:
        shot = row["shot"]
        text = row.get("action", "").strip()
        out = voice_dir / f"{shot}.wav"
        ok = False
        if text:
            ok = _sapi_speak(text, out, rate)
        if not ok:
            dur = float(row.get("duration_s", 1.0) or 1.0)
            _silence_wav(out, max(0.5, dur))
        generated.append({"shot": shot, "wav": str(out), "voice": bool(ok)})

    return {
        "status": "ok",
        "stage": "audio",
        "engine": "sapi",
        "shots": len(generated),
        "voice_count": sum(1 for g in generated if g["voice"]),
        "files": generated,
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="lab/projects/demo")
    ap.add_argument("--rate", type=int, default=1)
    args = ap.parse_args()
    print(json.dumps(run(Path(args.project), args.rate), ensure_ascii=False))
