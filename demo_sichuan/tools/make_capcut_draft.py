#!/usr/bin/env python3
"""Create a simple CapCut draft that opens the final Sichuan demo.

It copies the local CapCut OOBE draft as a structural template, then replaces
the video material with the final mp4. The draft is intentionally a single
clip: all cuts, subtitles, and color are already baked into the mp4. This gives
the editor a clean CapCut project for manual finishing without pretending to
recreate every CapCut internal object.
"""
from __future__ import annotations

import argparse
import json
import shutil
import uuid
from pathlib import Path

from PIL import Image


def new_id() -> str:
    return str(uuid.uuid4()).upper()


def load(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save(path: Path, data) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", default=None)
    ap.add_argument("--target", default=None)
    ap.add_argument("--video", required=True)
    ap.add_argument("--cover", required=True)
    ap.add_argument("--name", default="Sichuan30_一碗茶慢慢摆")
    args = ap.parse_args()

    if not args.template or not args.target:
        raise SystemExit(
            "--template and --target are required. Point them to your CapCut Drafts "
            "template and the output draft folder, e.g. --template \"D:\\...\\Drafts\\1020\" "
            "--target \"D:\\...\\Drafts\\Sichuan30\""
        )
    template = Path(args.template)
    target = Path(args.target)
    video = Path(args.video).resolve()
    cover = Path(args.cover).resolve()

    if not template.exists():
        raise SystemExit(f"template not found: {template}")
    if not video.exists():
        raise SystemExit(f"video not found: {video}")

    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(template, target)

    content_path = target / "draft_content.json"
    meta_path = target / "draft_meta_info.json"
    content = load(content_path)
    meta = load(meta_path)

    new_draft_id = new_id()
    duration = 30_000_000  # microseconds

    content["id"] = new_draft_id
    content["name"] = args.name
    content["duration"] = duration
    content["fps"] = 30.0
    content["canvas_config"]["width"] = 1280
    content["canvas_config"]["height"] = 720
    content["canvas_config"]["ratio"] = "16:9"

    # Keep only the main video track; drop the OOBE example effect track.
    tracks = [t for t in content.get("tracks", []) if t.get("type") == "video"]
    if not tracks:
        raise SystemExit("template has no video track")
    content["tracks"] = tracks
    seg = tracks[0]["segments"][0]
    seg["source_timerange"]["start"] = 0
    seg["source_timerange"]["duration"] = duration
    seg["target_timerange"]["start"] = 0
    seg["target_timerange"]["duration"] = duration
    seg["render_timerange"]["start"] = 0
    seg["render_timerange"]["duration"] = 0

    materials = content.setdefault("materials", {})
    videos = materials.get("videos") or []
    if not videos:
        raise SystemExit("template has no video material")
    old_video = videos[0]
    old_video["path"] = str(video).replace("\\", "/")
    old_video["media_path"] = ""
    old_video["duration"] = duration
    old_video["width"] = 1280
    old_video["height"] = 720
    old_video["material_name"] = video.name
    old_video["has_audio"] = True
    old_video["local_material_id"] = new_id()
    materials["videos"] = [old_video]
    materials["video_effects"] = []
    materials["effects"] = []

    # Remove references to the deleted effect material.
    for track in content["tracks"]:
        for segment in track.get("segments", []):
            refs = segment.get("extra_material_refs", [])
            segment["extra_material_refs"] = [
                r for r in refs if r != "29BD0504-3475-4183-8859-9DB6141FD4DF"
            ]

    save(content_path, content)

    meta["draft_id"] = new_draft_id
    meta["draft_name"] = args.name
    meta["draft_fold_path"] = str(target).replace("\\", "/")
    meta["draft_root_path"] = str(target.parent).replace("\\", "/")
    meta["draft_removable_storage_device"] = target.drive.replace("\\", "") or "D:"
    meta["tm_duration"] = duration
    meta["draft_cover"] = "draft_cover.jpg"
    save(meta_path, meta)

    # Cover
    img = Image.open(cover).convert("RGB")
    img.thumbnail((1280, 720))
    img.save(target / "draft_cover.jpg", quality=90)

    # Timestamp fields
    (target / "draft_settings").write_text(
        "[General]\ndraft_create_time=1792476812\ndraft_last_edit_time=1792480962\n"
        "real_edit_seconds=0\nreal_edit_keys=1\n",
        encoding="utf-8",
    )

    print(f"draft created: {target}")
    print(f"video: {video}")
    print(f"name: {args.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
