"""Stage 6: QC. Check duration, streams, size, and voice presence via ffprobe/ffmpeg."""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
from pathlib import Path


def find_ffprobe() -> str | None:
    exe = shutil.which("ffprobe")
    if exe:
        return exe
    # Next to any ffmpeg we can find (PATH, CapCut, imageio).
    ff = shutil.which("ffmpeg")
    if ff:
        probe = Path(ff).with_name("ffprobe.exe")
        if probe.exists():
            return str(probe)
    for root in [r"D:\Program Files\CapCut Drafts", r"D:\Program Files\CapCut",
                 r"D:\Program Files\JianyingPro"]:
        if Path(root).exists():
            for probe in Path(root).rglob("ffprobe.exe"):
                return str(probe)
    try:
        import imageio_ffmpeg  # type: ignore

        ff = Path(imageio_ffmpeg.get_ffmpeg_exe())
        probe = ff.with_name("ffprobe.exe")
        if probe.exists():
            return str(probe)
    except Exception:
        pass
    return None


def _probe(ffprobe: str, path: Path) -> dict:
    out = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries",
         "format=duration,size:stream=codec_type,codec_name,width,height",
         "-of", "json", str(path)],
        capture_output=True, timeout=60,
    ).stdout.decode("utf-8", "replace")
    try:
        return json.loads(out)
    except Exception:
        return {}


def _probe_via_ffmpeg(ffmpeg: str, path: Path) -> dict:
    """Fallback when ffprobe is missing: parse `ffmpeg -i` stderr."""
    import re

    p = subprocess.run([ffmpeg, "-i", str(path)], capture_output=True, timeout=60)
    err = p.stderr.decode("utf-8", "replace")
    duration = 0.0
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", err)
    if m:
        h, mi, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
        duration = h * 3600 + mi * 60 + s
    streams = []
    if "Video:" in err:
        streams.append({"codec_type": "video"})
    if "Audio:" in err:
        streams.append({"codec_type": "audio"})
    return {
        "format": {"duration": duration, "size": path.stat().st_size if path.exists() else 0},
        "streams": streams,
        "_via": "ffmpeg",
    }


def run(project: Path, expected_duration_s: float | None = None) -> dict:
    project = Path(project)
    final = project / "output" / "final.mp4"
    if not final.exists():
        raise FileNotFoundError("final.mp4 not found; run composite first")

    ffprobe = find_ffprobe()
    checks: list[dict] = []
    if ffprobe:
        info = _probe(ffprobe, final)
    else:
        # Fall back to ffmpeg itself (imageio-ffmpeg ships ffmpeg but not ffprobe).
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            try:
                import imageio_ffmpeg  # type: ignore

                ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            except Exception:
                ffmpeg = None
        if not ffmpeg:
            checks.append({"check": "probe", "ok": False, "detail": "neither ffprobe nor ffmpeg found"})
            return {"status": "warn", "stage": "qc", "checks": checks, "final": str(final)}
        info = _probe_via_ffmpeg(ffmpeg, final)
        checks.append({"check": "probe_backend", "ok": True, "detail": "ffmpeg (ffprobe unavailable)"})
    fmt = info.get("format", {})
    duration = float(fmt.get("duration", 0) or 0)
    size = int(fmt.get("size", 0) or 0)
    streams = info.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)

    checks.append({"check": "video_stream", "ok": bool(v), "detail": v.get("codec_name") if v else "missing"})
    checks.append({"check": "audio_stream", "ok": bool(a), "detail": a.get("codec_name") if a else "missing"})
    checks.append({"check": "size_bytes", "ok": size > 0, "detail": f"{size} bytes"})

    if expected_duration_s:
        tol = max(0.5, expected_duration_s * 0.05)
        ok = abs(duration - expected_duration_s) <= tol
        checks.append({"check": "duration", "ok": ok,
                       "detail": f"{duration:.2f}s vs expected {expected_duration_s:.2f}s"})
    else:
        checks.append({"check": "duration", "ok": duration > 0, "detail": f"{duration:.2f}s"})

    ok = all(c["ok"] for c in checks)
    return {
        "status": "ok" if ok else "fail",
        "stage": "qc",
        "final": str(final),
        "duration_s": round(duration, 2),
        "checks": checks,
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="lab/projects/demo")
    ap.add_argument("--expected-duration", type=float, default=None)
    args = ap.parse_args()
    print(json.dumps(run(Path(args.project), args.expected_duration), ensure_ascii=False))
