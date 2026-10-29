"""CLI orchestrator for the local AI video lab.

Usage:
  python lab\\run.py init --project lab\\projects\\demo
  python lab\\run.py import-script --input lab\\examples\\example_script.md --project lab\\projects\\demo
  python lab\\run.py storyboard --project lab\\projects\\demo
  python lab\\run.py audio --project lab\\projects\\demo
  python lab\\run.py composite --project lab\\projects\\demo
  python lab\\run.py qc --project lab\\projects\\demo
  python lab\\run.py all --project lab\\projects\\demo
  python lab\\run.py serve --port 8765
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB_DIR))

from stages import import_script, storyboard, audio, composite, qc  # noqa: E402


def stage_init(project: Path) -> dict:
    for sub in ["script", "output", "clips", "prompts", "audio/voice"]:
        (project / sub).mkdir(parents=True, exist_ok=True)
    (project / "manifest.json").touch(exist_ok=True)
    return {"status": "ok", "stage": "init", "project": str(project)}


def _default_project() -> Path:
    return LAB_DIR / "projects" / "demo"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="lab", description="本地 AI 视频制作实验室")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_project(p):
        p.add_argument("--project", default=str(_default_project()))
        return p

    add_project(sub.add_parser("init"))

    sp = add_project(sub.add_parser("import-script"))
    sp.add_argument("--input", required=True)

    sp = add_project(sub.add_parser("storyboard"))
    sp.add_argument("--template", default=None)

    sp = add_project(sub.add_parser("audio"))
    sp.add_argument("--rate", type=int, default=1)

    sp = add_project(sub.add_parser("composite"))
    sp.add_argument("--engine", default="wan_local")
    sp.add_argument("--fps", type=int, default=30)
    sp.add_argument("--width", type=int, default=1280)
    sp.add_argument("--height", type=int, default=720)
    sp.add_argument("--no-reuse", action="store_true")
    sp.add_argument("--steps", type=int, default=20)
    sp.add_argument("--max-frames", type=int, default=25)

    sp = add_project(sub.add_parser("qc"))
    sp.add_argument("--expected-duration", type=float, default=None)

    add_project(sub.add_parser("all"))

    sp = sub.add_parser("serve")
    sp.add_argument("--port", type=int, default=8765)

    args = ap.parse_args(argv)
    project = Path(getattr(args, "project", None) or _default_project())

    def p() -> Path:
        return project

    if args.cmd == "init":
        print(json.dumps(stage_init(p()), ensure_ascii=False))
    elif args.cmd == "import-script":
        print(json.dumps(import_script.run(p(), Path(args.input)), ensure_ascii=False))
    elif args.cmd == "storyboard":
        t = Path(args.template) if args.template else None
        print(json.dumps(storyboard.run(p(), t), ensure_ascii=False))
    elif args.cmd == "audio":
        print(json.dumps(audio.run(p(), args.rate), ensure_ascii=False))
    elif args.cmd == "composite":
        print(json.dumps(composite.run(p(), args.engine, args.fps, args.width, args.height,
                                       reuse=not args.no_reuse, steps=args.steps,
                                       max_frames=args.max_frames), ensure_ascii=False))
    elif args.cmd == "qc":
        print(json.dumps(qc.run(p(), args.expected_duration), ensure_ascii=False))
    elif args.cmd == "all":
        out = []
        out.append(stage_init(p()))
        out.append(import_script.run(p(), LAB_DIR / "examples" / "example_script.md"))
        out.append(storyboard.run(p()))
        out.append(audio.run(p()))
        out.append(composite.run(p()))
        out.append(qc.run(p(), expected_duration_s=out[4]["shots"] * 5.0))
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif args.cmd == "serve":
        from server import serve

        serve(args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
