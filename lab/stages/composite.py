"""Stage 5: composite. Assemble shots + voice into a final mp4 via FFmpeg.

Video engine is pluggable:
  - kenburns    -> animate a still keyframe (assets/keyframes/Sxx.*) with FFmpeg
                  zoompan; zero model/GPU. Falls back to a gradient card.
  - footage     -> real clips in assets/footage/Sxx.*; falls back to placeholder.
  - seedance    -> cloud Seedance (needs ARK_API_KEY / ARK_MODEL_ID).
  - wan_local   -> local Wan draft via ComfyUI; slow on CPU.
  - placeholder -> deterministic color clips (zero cost).
"""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
from pathlib import Path


def find_ffmpeg() -> str | None:
    """Locate ffmpeg via the shared resolver in stages.env.

    Order: FFMPEG_BIN env -> project bin/ -> PATH -> CapCut -> imageio-ffmpeg.
    Falls back to a local search if stages.env cannot be imported (direct run).
    """
    try:
        from stages import env as _env  # type: ignore

        return _env.find_ffmpeg()
    except Exception:
        pass
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    candidates = [
        Path(r"D:\Program Files\CapCut Drafts\..\CapCut\ffmpeg.exe"),
        Path(r"D:\Program Files\CapCut\ffmpeg.exe"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    try:
        import imageio_ffmpeg  # type: ignore

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _color_clip(ffmpeg: str, out: Path, seconds: float, idx: int, w: int, h: int, fps: int) -> bool:
    """Generate a deterministic placeholder color clip (H.264, silent)."""
    colors = ["0x223344", "0x442233", "0x334422", "0x443322", "0x224433"]
    color = colors[idx % len(colors)]
    cmd = [
        ffmpeg, "-y", "-f", "lavfi",
        "-i", f"color=c={color}:s={w}x{h}:r={fps}:d={seconds:.3f}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(out),
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=120)
        return r.returncode == 0 and out.exists()
    except Exception:
        return False


# ---- Real-footage engine (use shot real video when provided) ------------------
_FOOTAGE_EXTS = (".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".mts", ".ts")


def footage_path(project: Path, shot: str) -> Path | None:
    """Locate real footage for a shot in project/assets/footage/.

    Matches by shot id (S01.mp4 / S01.mov ...), case-insensitive. Returns the
    first match or None. This lets a user drop real filmed clips into the
    project and composite them directly (the "实拍素材" path).
    """
    foot_dir = Path(project) / "assets" / "footage"
    if not foot_dir.exists():
        return None
    for ext in _FOOTAGE_EXTS:
        for cand in (foot_dir / f"{shot}{ext}", foot_dir / f"{shot.lower()}{ext}"):
            if cand.exists():
                return cand
    # Fall back to any file whose stem starts with the shot id (e.g. S01_001.mp4).
    for f in sorted(foot_dir.iterdir()):
        if f.is_file() and f.suffix.lower() in _FOOTAGE_EXTS and f.stem.lower().startswith(shot.lower()):
            return f
    return None


def _footage_clip(ffmpeg: str, src: Path, out: Path, seconds: float, w: int, h: int, fps: int) -> bool:
    """Transcode a real clip to the project's output spec (scale/crop/pad + time)."""
    vf = f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,fps={fps}"
    cmd = [
        ffmpeg, "-y", "-i", str(src),
        "-vf", vf, "-t", f"{seconds:.3f}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(out),
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=300)
        return r.returncode == 0 and out.exists()
    except Exception:
        return False


# ---- Subtitles (drawtext) -----------------------------------------------------
_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",      # Microsoft YaHei (CJK)
    r"C:\Windows\Fonts\simhei.ttf",    # SimHei (CJK)
    r"C:\Windows\Fonts\arial.ttf",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]


def find_font() -> str | None:
    """Return a usable font file (CJK preferred), or None."""
    for f in _FONT_CANDIDATES:
        if Path(f).exists():
            return f
    return None


def _filter_path(p: str) -> str:
    """Escape a Windows path for use inside an FFmpeg filter option."""
    return p.replace("\\", "/").replace(":", r"\:")


def _add_subtitle(ffmpeg: str, clip: Path, text: str, w: int, h: int,
                  font: str, fps: int) -> bool:
    """Burn one subtitle line onto a clip (re-encode, keeps duration)."""
    text = (text or "").strip()
    if not text:
        return True
    txt = clip.with_name(clip.stem + ".subtitle.txt")
    txt.write_text(text, encoding="utf-8")
    size = max(14, h // 22)
    vf = (
        f"drawtext=fontfile='{_filter_path(font)}':textfile='{_filter_path(str(txt.resolve()))}':"
        f"fontcolor=white:fontsize={size}:line_spacing=6:"
        f"box=1:boxcolor=black@0.45:boxborderw=8:"
        f"x=(w-text_w)/2:y=h-text_h-{max(16, h // 16)}"
    )
    tmp = clip.with_name(clip.stem + ".sub.mp4")
    cmd = [
        ffmpeg, "-y", "-i", str(clip), "-vf", vf,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps), "-an", str(tmp),
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=300)
        if r.returncode == 0 and tmp.exists() and tmp.stat().st_size > 0:
            tmp.replace(clip)
            txt.unlink(missing_ok=True)
            return True
    except Exception:
        pass
    try:
        txt.unlink(missing_ok=True)
        tmp.unlink(missing_ok=True)
    except OSError:
        pass
    return False


# ---- Crossfade transitions (xfade) -------------------------------------------
XFADE_MAP = {
    "none": None,
    "fade": "fade",
    "dissolve": "fade",
    "wipeleft": "wipeleft",
    "wiperight": "wiperight",
    "slideleft": "slideleft",
    "slideup": "slideup",
    "circleopen": "circleopen",
}


def _concat_xfade(ffmpeg: str, clips: list[str], durations: list[float],
                  transition: str, fade: float, out: Path,
                  w: int, h: int, fps: int) -> bool:
    """Join clips with xfade transitions (re-encode)."""
    n = len(clips)
    if n < 2:
        return False
    mode = XFADE_MAP.get(transition, "fade")
    if not mode:
        return False
    fade = max(0.1, min(fade, min(durations) / 3.0))

    inputs: list[str] = []
    for c in clips:
        inputs += ["-i", c]

    parts = []
    for i in range(n):
        parts.append(
            f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,"
            f"setpts=PTS-STARTPTS,fps={fps},settb=AVTB,"
            f"format=yuv420p[v{i}]"
        )
    prev = "v0"
    cum = durations[0]
    for k in range(1, n):
        offset = cum - k * fade
        if offset < 0.05:
            offset = 0.05
        label = f"x{k}"
        parts.append(
            f"[{prev}][v{k}]xfade=transition={mode}:duration={fade:.3f}:"
            f"offset={offset:.3f}[{label}]"
        )
        prev = label
        cum += durations[k]
    graph = ";".join(parts)
    cmd = [
        ffmpeg, "-y", *inputs, "-filter_complex", graph, "-map", f"[{prev}]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
        "-movflags", "+faststart", str(out),
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=1200)
        return r.returncode == 0 and out.exists() and out.stat().st_size > 0
    except Exception:
        return False


def run(project: Path, engine: str = "wan_local", fps: int = 30, width: int = 1280, height: int = 720,
        reuse: bool = True, steps: int = 20, max_frames: int = 25,
        transition: str = "none", xfade: float = 0.5, subtitles: bool = False) -> dict:
    project = Path(project)
    shot_list = project / "shot_list.csv"
    if not shot_list.exists():
        raise FileNotFoundError("shot_list.csv not found; run storyboard first")

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found; install ffmpeg or CapCut")

    rows = list(csv.DictReader(shot_list.open(encoding="utf-8-sig")))
    if not rows:
        raise RuntimeError("shot_list.csv is empty")

    clips_dir = project / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    # Detect engine readiness: local Wan (models + server up) or cloud Seedance (creds).
    wan_ready = False
    try:
        import wan  # type: ignore

        wan_ready = engine == "wan_local" and wan.models_ready() and wan.server_running()
    except Exception:
        wan_ready = False
    cloud_ready = False
    try:
        from stages import seedance  # type: ignore

        cloud_ready = engine == "seedance" and seedance.is_ready()
    except Exception:
        cloud_ready = False

    clip_files = []
    durations: list[float] = []
    engine_used = "placeholder"
    for i, row in enumerate(rows):
        shot = row["shot"]
        seconds = float(row.get("duration_s", 5.0) or 5.0)
        out = clips_dir / f"{shot}.mp4"
        if reuse and out.exists():
            # Deterministic re-runs: keep an already-rendered clip.
            engine_used = "reuse"
        elif engine == "footage":
            # Real-footage path: use provided shot video, else fall back.
            src = footage_path(project, shot)
            if src and _footage_clip(ffmpeg, src, out, seconds, width, height, fps):
                engine_used = "footage"
            else:
                _color_clip(ffmpeg, out, seconds, i, width, height, fps)
        elif engine == "kenburns":
            # Keyframe motion path: animate a still (or a gradient card).
            from stages import kenburns  # type: ignore

            res = kenburns.render(
                ffmpeg, project, shot, out, seconds, width, height, fps,
                camera=row.get("camera", "缓慢推近"), card_index=i,
            )
            if res.get("status") == "ok":
                engine_used = "kenburns"
            else:
                _color_clip(ffmpeg, out, seconds, i, width, height, fps)
        elif cloud_ready:
            from stages import seedance  # type: ignore

            prompt_file = project / row.get("prompt_file", "")
            prompt_text = (prompt_file.read_text(encoding="utf-8") if prompt_file.exists()
                           else row.get("action", "a cinematic scene"))
            # First-frame image (I2V) if the project has keyframes for this shot.
            keyframe = project / "assets" / "keyframes" / f"{shot}.png"
            res = seedance.render(prompt_text, out, image=keyframe if keyframe.exists() else None,
                                  duration=int(seconds), timeout_s=900)
            if res.get("status") == "ok" and out.exists():
                engine_used = "seedance"
            else:
                _color_clip(ffmpeg, out, seconds, i, width, height, fps)
        elif wan_ready:
            import wan  # type: ignore

            # Draft mode: keep it cheap on CPU (short clip, few steps).
            prompt_file = project / row.get("prompt_file", "")
            prompt_text = (prompt_file.read_text(encoding="utf-8") if prompt_file.exists()
                           else row.get("action", "a scene, cinematic"))
            webm = clips_dir / f"{shot}.webm"
            # Full-duration frames (4k+1) capped by max_frames; more steps = less mushy.
            frames = min(max_frames, int(seconds * 16) + 1)
            res = wan.render(prompt_text, webm, frames=frames, steps=steps)
            if res.get("status") == "ok" and webm.exists():
                subprocess.run([ffmpeg, "-y", "-i", str(webm), "-c:v", "libx264",
                                "-pix_fmt", "yuv420p", str(out)], capture_output=True, timeout=300)
                engine_used = "wan_local"
            else:
                _color_clip(ffmpeg, out, seconds, i, width, height, fps)
        else:
            _color_clip(ffmpeg, out, seconds, i, width, height, fps)
        clip_files.append(str(out))
        durations.append(seconds)

    subtitle_note = None
    if subtitles:
        font = find_font()
        if not font:
            subtitle_note = "no CJK font found; subtitles skipped"
        else:
            for row, clip in zip(rows, clip_files):
                text = row.get("subtitle") or row.get("caption") or ""
                if text.strip():
                    _add_subtitle(ffmpeg, Path(clip), text, width, height, font, fps)

    # Join clips: default concat demuxer; optional xfade crossfade (re-encode).
    concat_list = project / "clips" / "concat.txt"
    # Use ABSOLUTE paths: ffmpeg resolves relative paths against concat.txt's dir,
    # so relative entries would double the path and fail to open.
    concat_list.write_text(
        "".join(f"file '{Path(c).resolve().as_posix()}'\n" for c in clip_files), encoding="utf-8"
    )
    video_out = project / "output" / "video_silent.mp4"
    video_out.parent.mkdir(parents=True, exist_ok=True)
    used_transition = "none"
    if transition and transition != "none" and len(clip_files) > 1:
        if _concat_xfade(ffmpeg, clip_files, durations, transition, xfade,
                         video_out, width, height, fps):
            used_transition = transition
    if used_transition == "none":
        subprocess.run(
            [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video_out)],
            capture_output=True, timeout=600,
        )

    # Voice: build a single mixed audio track from each shot's voice wav.
    voice_dir = project / "audio" / "voice"
    audio_in = []
    for row in rows:
        wav = voice_dir / f"{row['shot']}.wav"
        if wav.exists():
            audio_in.append(str(wav))
    audio_track = project / "output" / "voice_mix.m4a"
    if audio_in:
        subprocess.run(
            [ffmpeg, "-y"] + [a for w in audio_in for a in ("-i", w)] +
            ["-filter_complex", f"{''.join(f'[{i}:a]' for i in range(len(audio_in)))}"
             f"concat=n={len(audio_in)}:v=0:a=1[out]", "-map", "[out]",
             "-c:a", "aac", "-b:a", "128k", str(audio_track)],
            capture_output=True, timeout=300,
        )

    # Final mux.
    final = project / "output" / "final.mp4"
    cmd = [ffmpeg, "-y", "-i", str(video_out)]
    if audio_track.exists():
        cmd += ["-i", str(audio_track), "-c:v", "copy", "-c:a", "aac", "-shortest"]
    else:
        cmd += ["-c:v", "copy", "-an"]
    cmd += [str(final)]
    subprocess.run(cmd, capture_output=True, timeout=600)

    return {
        "status": "ok",
        "stage": "composite",
        "engine": engine,
        "engine_used": engine_used,
        "shots": len(clip_files),
        "transition": used_transition,
        "subtitles": bool(subtitles),
        "subtitle_note": subtitle_note,
        "final": str(final),
        "ffmpeg": ffmpeg,
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="lab/projects/demo")
    ap.add_argument("--engine", default="wan_local")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--no-reuse", action="store_true")
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--max-frames", type=int, default=25)
    ap.add_argument("--transition", default="none", help="none|fade|wipeleft|slideleft|circleopen")
    ap.add_argument("--xfade", type=float, default=0.5, help="transition duration seconds")
    ap.add_argument("--subtitles", action="store_true", help="burn subtitle/caption column")
    args = ap.parse_args()
    print(json.dumps(run(Path(args.project), args.engine, args.fps, args.width, args.height,
                         reuse=not args.no_reuse, steps=args.steps, max_frames=args.max_frames,
                         transition=args.transition, xfade=args.xfade,
                         subtitles=args.subtitles),
                     ensure_ascii=False))
