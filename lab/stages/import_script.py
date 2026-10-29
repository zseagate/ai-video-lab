"""Stage 2: import a script (markdown/txt) into a lab project manifest."""
from __future__ import annotations

import json
import re
from pathlib import Path


def parse_script(text: str) -> dict:
    lines = text.splitlines()
    title = ""
    logline = ""
    for line in lines:
        s = line.strip()
        if not title and s.startswith("# "):
            title = s[2:].strip()
        elif not logline and s and not s.startswith("#"):
            logline = s
            break

    scenes: list[dict] = []
    current: dict | None = None
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith("## "):
            if current:
                scenes.append(current)
            current = {"title": s[3:].strip(), "lines": []}
        elif not s.startswith("#") and current is not None:
            # Only collect body text after a scene heading; preamble/logline skipped.
            current["lines"].append(s)
    if current:
        scenes.append(current)

    if not scenes:
        paras = re.split(r"\n\s*\n", text)
        for i, p in enumerate(paras):
            if p.strip() and not p.strip().startswith("#"):
                scenes.append({"title": f"场景 {i + 1}", "lines": [p.strip()]})

    return {"title": title or "未命名项目", "logline": logline, "scenes": scenes}


def run(project: Path, input_file: Path, template: Path | None = None) -> dict:
    project = Path(project)
    input_file = Path(input_file)
    if not input_file.exists():
        raise FileNotFoundError(f"input script not found: {input_file}")

    (project / "script").mkdir(parents=True, exist_ok=True)
    (project / "output").mkdir(parents=True, exist_ok=True)
    (project / "audio" / "voice").mkdir(parents=True, exist_ok=True)

    text = input_file.read_text(encoding="utf-8-sig")
    manifest = parse_script(text)
    manifest["source"] = str(input_file)
    manifest["scene_count"] = len(manifest["scenes"])

    (project / "script" / "script.md").write_text(text, encoding="utf-8")
    (project / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {
        "status": "ok",
        "stage": "import-script",
        "title": manifest["title"],
        "logline": manifest["logline"],
        "scene_count": manifest["scene_count"],
        "manifest": str(project / "manifest.json"),
    }


if __name__ == "__main__":
    import argparse
    import sys

    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--project", default="lab/projects/demo")
    args = ap.parse_args()
    print(json.dumps(run(Path(args.project), Path(args.input)), ensure_ascii=False))
