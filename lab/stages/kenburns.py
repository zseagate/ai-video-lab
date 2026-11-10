"""Ken Burns / keyframe motion engine: still image -> moving shot.

FFmpeg-only. No model, no GPU, no inference. A 5s shot renders in a few seconds
on a 4-core CPU, so this is the low-spec way to get real motion into a cut.

Frame sources (first match wins):
  1. project/assets/keyframes/<shot>.<png|jpg|jpeg|webp|bmp>
  2. a generated gradient card (a placeholder that still moves)

Motion is chosen from the shot's `camera` field (the same Chinese vocabulary
used by promptgen.CAMERA_MOVE).

Jitter note: zoompan recipes that accumulate `zoom+0.0015` quantise the zoom to
a few discrete steps (FFmpeg trac #4298). We compute zoom/pan *absolutely* from
the output-frame counter `on`, which is smooth.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")

# camera key -> (zoom0, zoom1, (x0, x1), (y0, y1))
# x/y are normalised pan centres in 0..1, interpolated over the shot.
MOTIONS: dict[str, tuple[float, float, tuple[float, float], tuple[float, float]]] = {
    "slow_push_in": (1.00, 1.15, (0.5, 0.5), (0.5, 0.5)),
    "push_in": (1.00, 1.25, (0.5, 0.5), (0.5, 0.5)),
    "slow_pull_back": (1.15, 1.00, (0.5, 0.5), (0.5, 0.5)),
    "pull_back": (1.25, 1.00, (0.5, 0.5), (0.5, 0.5)),
    "lateral": (1.12, 1.12, (0.0, 1.0), (0.5, 0.5)),
    "orbit": (1.12, 1.12, (0.10, 0.90), (0.5, 0.5)),
    "static": (1.02, 1.02, (0.5, 0.5), (0.5, 0.5)),
    "handheld": (1.03, 1.06, (0.48, 0.52), (0.48, 0.52)),
    "following": (1.05, 1.15, (0.5, 0.5), (0.40, 0.60)),
    "crane_rise": (1.00, 1.15, (0.5, 0.5), (0.70, 0.30)),
}

# Chinese storyboard label -> motion key.
ZH_TO_KEY = {
    "缓慢推近": "slow_push_in",
    "推近": "push_in",
    "缓慢拉远": "slow_pull_back",
    "拉远": "pull_back",
    "横移": "lateral",
    "环绕": "orbit",
    "固定": "static",
    "手持": "handheld",
    "跟随": "following",
    "上升": "crane_rise",
}

DEFAULT_MOTION = "slow_push_in"


def resolve_motion(camera: str | None) -> tuple[str, tuple]:
    """Return (motion_key, params) for a Chinese label or English key."""
    key = str(camera or "").strip()
    if key in MOTIONS:
        return key, MOTIONS[key]
    mapped = ZH_TO_KEY.get(key)
    if mapped:
        return mapped, MOTIONS[mapped]
    return DEFAULT_MOTION, MOTIONS[DEFAULT_MOTION]


def keyframe_path(project: Path, shot: str) -> Path | None:
    """Locate a user-supplied keyframe image for a shot."""
    kdir = Path(project) / "assets" / "keyframes"
    if not kdir.exists():
        return None
    for ext in IMAGE_EXTS:
        for cand in (kdir / f"{shot}{ext}", kdir / f"{shot.lower()}{ext}"):
            if cand.exists():
                return cand
    for f in sorted(kdir.iterdir()):
        if f.is_file() and f.suffix.lower() in IMAGE_EXTS and f.stem.lower().startswith(shot.lower()):
            return f
    return None


def _make_card(ffmpeg: str, out: Path, w: int, h: int, idx: int) -> bool:
    """Generate a gradient placeholder card (still image) with FFmpeg."""
    palettes = [
        ("0x1b2a4a", "0x3a1b2a"),
        ("0x1b3a2a", "0x3a2a1b"),
        ("0x2a1b3a", "0x1b2a3a"),
        ("0x3a1b2a", "0x2a3a1b"),
        ("0x223344", "0x443322"),
    ]
    c0, c1 = palettes[idx % len(palettes)]
    attempts = [
        [
            ffmpeg, "-y", "-f", "lavfi",
            "-i", f"gradients=s={w}x{h}:c0={c0}:c1={c1}:d=1",
            "-frames:v", "1", str(out),
        ],
        [
            ffmpeg, "-y", "-f", "lavfi",
            "-i", f"color=c={c0}:s={w}x{h}:d=1",
            "-frames:v", "1", str(out),
        ],
    ]
    for cmd in attempts:
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=60)
            if r.returncode == 0 and out.exists() and out.stat().st_size > 0:
                return True
        except Exception:
            continue
    return False


def _build_filter(z0: float, z1: float, x0: float, x1: float,
                  y0: float, y1: float, frames: int,
                  width: int, height: int, fps: int, seconds: float) -> str:
    maxz = max(z0, z1)
    den = max(1, frames - 1)
    zexpr = f"{z0:.4f}+({z1 - z0:.4f})*on/{den}"
    xexpr = f"(iw-iw/zoom)*({x0:.4f}+({x1 - x0:.4f})*on/{den})"
    yexpr = f"(ih-ih/zoom)*({y0:.4f}+({y1 - y0:.4f})*on/{den})"
    pre_w = int(round(width * maxz))
    pre_h = int(round(height * maxz))
    return (
        f"scale={pre_w}:{pre_h}:force_original_aspect_ratio=increase,"
        f"crop={pre_w}:{pre_h},"
        f"zoompan=z='{zexpr}':x='{xexpr}':y='{yexpr}':"
        f"d={frames}:s={width}x{height}:fps={fps},"
        f"setsar=1,trim=duration={seconds:.3f},setpts=PTS-STARTPTS"
    )


def render(ffmpeg: str, project: Path, shot: str, out: Path, seconds: float,
           width: int, height: int, fps: int, camera: str = "缓慢推近",
           card_index: int = 0) -> dict:
    """Render one Ken Burns clip. Returns a status dict."""
    project = Path(project)
    out = Path(out)
    src = keyframe_path(project, shot)
    using_card = src is None
    motion_key, (z0, z1, (x0, x1), (y0, y1)) = resolve_motion(camera)
    frames = max(2, int(round(seconds * fps)))

    with tempfile.TemporaryDirectory() as td:
        if src is None:
            src = Path(td) / "card.png"
            if not _make_card(ffmpeg, src, width, height, card_index):
                return {"status": "error", "shot": shot, "reason": "gradient card failed (need ffmpeg>=7)"}

        vf = _build_filter(z0, z1, x0, x1, y0, y1, frames, width, height, fps, seconds)
        cmd = [
            ffmpeg, "-y", "-i", str(src),
            "-vf", vf,
            "-frames:v", str(frames), "-r", str(fps),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an",
            "-movflags", "+faststart", str(out),
        ]
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=300)
            ok = r.returncode == 0 and out.exists() and out.stat().st_size > 0
            return {
                "status": "ok" if ok else "error",
                "shot": shot,
                "source": "card" if using_card else "keyframe",
                "motion": motion_key,
                "reason": None if ok else r.stderr.decode("utf-8", "ignore")[-400:],
            }
        except Exception as e:
            return {"status": "error", "shot": shot, "reason": str(e)}
