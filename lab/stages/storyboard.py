"""Stage 3: build a storyboard (shot list + Seedance prompts + storyboard markdown).

This is the "剧本拆分分镜 + 自动生成 Seedance 提示词" stage. Each scene is
split into 1..N shots based on action beats (特写/开启/蒙太奇/转场/收束), and
every shot gets a structured, optimised Seedance prompt (see promptgen.py).

Prompt workflow knobs (rules-based, offline):
  - auto: regenerate every shot's prompt from its row (default).
  - keep: keep existing prompt files if present (deterministic re-runs).
"""
from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import promptgen

HEADER = [
    "shot", "start_s", "end_s", "duration_s", "scene",
    "shot_size", "camera", "action", "light", "audio", "function", "prompt_file",
]

# Beat -> (shot_size, camera, duration_s). Tuned for a 5s-per-shot rhythm.
BEAT_SHOT = {
    "细节特写": ("特写", "缓慢推近", 3.0),
    "动作开启": ("中景", "缓慢推近", 4.0),
    "节奏蒙太奇": ("近景", "横移", 2.5),
    "转场运动": ("全景", "跟随", 4.0),
    "收束定格": ("中近景", "缓慢拉远", 4.0),
    "叙事": ("中景", "缓慢推近", 5.0),
}


def split_scene_shots(scene: dict) -> list[dict]:
    """Split one scene into shot descriptors using action beats."""
    action = " ".join(scene.get("lines", [])).strip() or scene.get("title", "")
    beats = promptgen.detect_beats(action)
    shots = []
    # Multiple beats -> multiple shots (e.g. 特写 + 蒙太奇 + 收束).
    for b in beats:
        size, cam, dur = BEAT_SHOT.get(b, BEAT_SHOT["叙事"])
        shots.append({
            "shot_size": size, "camera": cam, "duration_s": dur,
            "action": action, "function": b, "light": "暖色灯光",
        })
    return shots


def _default_light(action: str, scene_title: str) -> str:
    for kw in ("雨", "夜", "霓虹", "暗"):
        if kw in action or kw in scene_title:
            return "夜景" if kw == "夜" else "暖色灯光"
    return "暖色灯光"


def run(project: Path, template: Path | None = None, mode: str = "auto") -> dict:
    project = Path(project)
    manifest_path = project / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError("manifest.json not found; run import-script first")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scenes = manifest.get("scenes", [])
    if not scenes:
        raise RuntimeError("no scenes in manifest")

    prompts_dir = project / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    # Cross-scene consistency anchors: auto-extract once, reuse for every shot.
    style = promptgen.load_style(project, manifest)

    rows = []
    shot_idx = 0
    start = 0.0
    for i, sc in enumerate(scenes):
        scene_title = sc.get("title", "")
        scene_action = " ".join(sc.get("lines", [])).strip() or scene_title
        # Split the scene into 1..N shots by action beats.
        for sd in split_scene_shots(sc):
            shot_idx += 1
            name = f"S{shot_idx:02d}"
            dur = float(sd["duration_s"])
            end = round(start + dur, 2)
            light = _default_light(scene_action, scene_title)
            rows.append([
                name, f"{start:.2f}", f"{end:.2f}", f"{dur:.2f}",
                scene_title, sd["shot_size"], sd["camera"], sd["action"],
                light, "beat", sd["function"], f"prompts/{name}.txt",
            ])
            # Prompt file: template -> keep existing (mode=keep) -> auto-generate.
            prompt_file = prompts_dir / f"{name}.txt"
            if template and (template / f"{name}.txt").exists():
                shutil.copy(template / f"{name}.txt", prompt_file)
            elif mode == "keep" and prompt_file.exists():
                pass
            else:
                shot_row = {
                    "shot": name, "shot_size": sd["shot_size"], "camera": sd["camera"],
                    "action": sd["action"], "light": light, "scene": scene_title,
                    "duration_s": dur,
                }
                prompt_file.write_text(promptgen.generate(shot_row, manifest, style), encoding="utf-8")
            start = end

    shot_list = project / "shot_list.csv"
    with shot_list.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(rows)

    # Storyboard markdown with per-shot prompt previews.
    md = [f"# 故事板 · {manifest.get('title', '')}", "", f"> {manifest.get('logline', '')}", ""]
    for r in rows:
        prompt_file = project / r[11]
        preview = (prompt_file.read_text(encoding="utf-8").splitlines()[0]
                   if prompt_file.exists() else "")
        md.append(f"## {r[0]}  {r[4]}")
        md.append(f"- 时间：{r[1]}–{r[2]}s（{r[3]}s）· {r[9]}")
        md.append(f"- 景别/运镜：{r[5]} / {r[6]}")
        md.append(f"- 功能：{r[10]}")
        md.append(f"- 动作：{r[7]}")
        md.append(f"- 提示词：{preview}")
        md.append("")
    (project / "storyboard.md").write_text("\n".join(md), encoding="utf-8")

    return {
        "status": "ok",
        "stage": "storyboard",
        "shots": len(rows),
        "scenes": len(scenes),
        "total_duration_s": round(start, 2),
        "shot_list": str(shot_list),
        "storyboard": str(project / "storyboard.md"),
        "prompt_mode": mode,
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="lab/projects/demo")
    ap.add_argument("--template", default=None)
    ap.add_argument("--mode", default="auto", choices=["auto", "keep"])
    args = ap.parse_args()
    t = Path(args.template) if args.template else None
    print(json.dumps(run(Path(args.project), t, args.mode), ensure_ascii=False))
