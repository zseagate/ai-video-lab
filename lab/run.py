"""CLI orchestrator for the local AI video lab.

Usage:
  python lab\\run.py init --project lab\\projects\\demo
  python lab\\run.py import-script --input lab\\examples\\example_script.md --project lab\\projects\\demo
  python lab\\run.py storyboard --project lab\\projects\\demo
  python lab\\run.py audio --project lab\\projects\\demo
  python lab\\run.py composite --project lab\\projects\\demo
  python lab\\run.py qc --project lab\\projects\\demo
  python lab\\run.py all --project lab\\projects\\demo
  python lab\\run.py doctor
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
sys.path.insert(0, str(LAB_DIR / "stages"))

from stages import import_script, storyboard, audio, composite, qc, env  # noqa: E402


def stage_init(project: Path) -> dict:
    for sub in ["script", "output", "clips", "prompts", "audio/voice",
                "assets/keyframes", "assets/footage"]:
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
    sp.add_argument("--engine", default=None)
    sp.add_argument("--fps", type=int, default=None)
    sp.add_argument("--width", type=int, default=None)
    sp.add_argument("--height", type=int, default=None)
    sp.add_argument("--no-reuse", action="store_true")
    sp.add_argument("--steps", type=int, default=20)
    sp.add_argument("--max-frames", type=int, default=25)

    sp = add_project(sub.add_parser("qc"))
    sp.add_argument("--expected-duration", type=float, default=None)

    add_project(sub.add_parser("all"))

    sub.add_parser("doctor")

    sp = sub.add_parser("models")
    sp.add_argument("--list", action="store_true")
    sp.add_argument("--download", default=None, metavar="NAME")

    sp = sub.add_parser("low-spec")
    sp.add_argument("--on", action="store_true")
    sp.add_argument("--off", action="store_true")

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
        d = env.composite_defaults()
        print(json.dumps(composite.run(
            p(),
            args.engine or d["engine"],
            args.fps or d["fps"],
            args.width or d["width"],
            args.height or d["height"],
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
        d = env.composite_defaults()
        out.append(composite.run(p(), d["engine"], d["fps"], d["width"], d["height"]))
        expected = out[2].get("total_duration_s") or out[4]["shots"] * 5.0
        out.append(qc.run(p(), expected_duration_s=expected))
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif args.cmd == "doctor":
        report = env.doctor()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        print()
        print("== local readiness ==")
        print(f"python   : {report['python']}")
        print(f"ffmpeg   : {report['ffmpeg'] or 'NOT FOUND'}")
        if report.get("ffmpeg_version"):
            print(f"           {report['ffmpeg_version']}")
        print(f"llama_cpp: {report['llama_cpp'] or 'not installed (optional)'}")
        models = report.get("gguf_models") or []
        print(f"gguf     : {len(models)} model(s) in {report['models_dir']}")
        for name in models[:10]:
            print(f"           - {name}")
        print("engines  :")
        for name, state in report["engines"].items():
            print(f"           {name:11s} {state}")
    elif args.cmd == "models":
        from stages import models

        if args.download:
            print(json.dumps(models.download(args.download), ensure_ascii=False, indent=2))
        else:
            print(json.dumps(models.status(), ensure_ascii=False, indent=2))
    elif args.cmd == "low-spec":
        current = env.load_settings()
        if args.on:
            current = env.save_settings({"enabled": True})
        elif args.off:
            current = env.save_settings({"enabled": False})
        print(json.dumps({"settings": current,
                          "defaults": env.composite_defaults()},
                         ensure_ascii=False, indent=2))
    elif args.cmd == "serve":
        from server import serve

        serve(args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
