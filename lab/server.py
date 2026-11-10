"""Local web management console for the video lab (stdlib only, no deps).

Provides a graphical dashboard (static/index.html) + a small JSON API:
  projects / status / engines / run/<stage> / file / config / project new
Run: python lab\\server.py --port 8765  ->  http://127.0.0.1:8765
"""
from __future__ import annotations

import json
import base64
import shutil
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB_DIR))
sys.path.insert(0, str(LAB_DIR / "stages"))

import stages.import_script as import_script  # noqa: E402
import stages.storyboard as storyboard  # noqa: E402
import stages.promptgen as promptgen  # noqa: E402
import stages.audio as audio  # noqa: E402
import stages.composite as composite  # noqa: E402
import stages.qc as qc  # noqa: E402
import stages.env as lab_env  # noqa: E402
import stages.models as lab_models  # noqa: E402
import stages.llm_enhance as llm_enhance  # noqa: E402
import stages.kenburns as kenburns  # noqa: E402
import stages.cost as cost  # noqa: E402

STATIC = LAB_DIR / "static"
PROJECTS = LAB_DIR / "projects"

ALLOWED_FILES = {"storyboard.md", "shot_list.csv", "manifest.json", "README.md"}
MAX_SCRIPT_BYTES = 2 * 1024 * 1024  # 2 MB script cap


def run_stage(name: str, project: Path) -> dict:
    if name == "init":
        for sub in ["script", "output", "clips", "prompts", "audio/voice",
                    "assets/keyframes", "assets/footage"]:
            (project / sub).mkdir(parents=True, exist_ok=True)
        (project / "manifest.json").touch(exist_ok=True)
        return {"status": "ok", "stage": "init"}
    if name == "import-script":
        example = LAB_DIR / "examples" / "example_script.md"
        return import_script.run(project, example)
    if name == "storyboard":
        return storyboard.run(project)
    if name == "audio":
        return audio.run(project)
    if name == "composite":
        d = lab_env.composite_defaults()
        return composite.run(project, engine=d["engine"], fps=d["fps"],
                             width=d["width"], height=d["height"])
    if name == "qc":
        return qc.run(project)
    raise ValueError(f"unknown stage: {name}")


def project_status(project: Path) -> dict:
    def done(f: str) -> bool:
        return (project / f).exists()

    final = project / "output" / "final.mp4"
    return {
        "project": project.name,
        "stages": {
            "init": {"done": (project / "manifest.json").exists()},
            "import-script": {"done": done("manifest.json")},
            "storyboard": {"done": done("shot_list.csv")},
            "audio": {"done": any((project / "audio" / "voice").glob("*.wav")) if (project / "audio" / "voice").exists() else False},
            "composite": {"done": final.exists()},
            "qc": {"done": (project / "output" / "qc.json").exists()},
        },
        "final": {
            "exists": final.exists(),
            "path": str(final) if final.exists() else None,
            "size": final.stat().st_size if final.exists() else 0,
        },
        "files": {
            "storyboard": (project / "storyboard.md").exists(),
            "shot_list": (project / "shot_list.csv").exists(),
            "manifest": (project / "manifest.json").exists(),
        },
    }


def _load_manifest(project: Path) -> dict:
    p = project / "manifest.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def list_shots(project: Path) -> list[dict]:
    """Return each shot row + its prompt text (for the prompt workbench)."""
    shot_list = project / "shot_list.csv"
    if not shot_list.exists():
        return []
    import csv as _csv

    shots = []
    for row in _csv.DictReader(shot_list.open(encoding="utf-8-sig")):
        pf = project / row.get("prompt_file", "")
        shots.append({
            "shot": row.get("shot", ""),
            "scene": row.get("scene", ""),
            "shot_size": row.get("shot_size", ""),
            "camera": row.get("camera", ""),
            "action": row.get("action", ""),
            "function": row.get("function", ""),
            "duration_s": row.get("duration_s", ""),
            "prompt": pf.read_text(encoding="utf-8") if pf.exists() else "",
        })
    return shots


def engine_status() -> dict:
    out = {"ffmpeg": {"ready": bool(composite.find_ffmpeg())},
           "footage": {"ready": False, "clips": 0},
           "kenburns": {"ready": True, "note": "FFmpeg zoompan, no model"},
           "wan": {"ready": False}, "seedance": {"ready": False}}
    try:
        import wan  # type: ignore

        out["wan"] = {"ready": wan.models_ready() and wan.server_running(),
                      "models": wan.models_ready(), "server": wan.server_running(),
                      "comfy": str(wan.find_comfy()) if wan.find_comfy() else None}
    except Exception:
        pass
    try:
        # Real-footage engine: count clips found in any project's assets/footage.
        foot_dir = PROJECTS / "_footage_check"
        count = 0
        for proj in PROJECTS.iterdir():
            if proj.is_dir() and (proj / "assets" / "footage").exists():
                count += len([f for f in (proj / "assets" / "footage").iterdir()
                              if f.is_file() and f.suffix.lower() in composite._FOOTAGE_EXTS])
        out["footage"] = {"ready": count > 0, "clips": count}
    except Exception:
        pass
    try:
        from stages import seedance  # type: ignore

        out["seedance"] = {"ready": seedance.is_ready()}
    except Exception:
        pass
    try:
        out["llm"] = llm_enhance.status()
    except Exception:
        out["llm"] = {"available": False}
    try:
        out["models"] = {
            "installed": [m["name"] for m in lab_models.status() if m["installed"]],
            "any": lab_models.resolve_default() is not None,
        }
    except Exception:
        out["models"] = {"installed": [], "any": False}
    return out


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # quiet
        pass

    def _json(self, obj, code: int = 200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path: Path, ctype: str):
        if not path.exists():
            self._json({"error": "missing"}, 404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _project(self, query) -> Path:
        name = query.get("project", ["demo"])[0]
        name = Path(name).name  # sanitize: no traversal
        return PROJECTS / name

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        path = parsed.path
        if path == "/api/health":
            self._json({"status": "ok", "service": "video-lab"})
        elif path == "/api/projects":
            names = sorted(
                p.name for p in PROJECTS.iterdir()
                if p.is_dir() and not p.name.startswith(".") and p.name != "__pycache__"
            )
            self._json({"projects": names})
        elif path == "/api/status":
            self._json(project_status(self._project(query)))
        elif path == "/api/engines":
            self._json(engine_status())
        elif path == "/api/shots":
            self._json({"shots": list_shots(self._project(query))})
        elif path == "/api/style":
            proj = self._project(query)
            manifest = _load_manifest(proj)
            style = promptgen.load_style(proj, manifest)
            self._json({"style": style, "file": str(promptgen.style_path(proj))})
        elif path == "/api/config":
            cfg = LAB_DIR / "config.yaml"
            self._file(cfg, "text/plain; charset=utf-8")
        elif path == "/api/settings":
            self._json({"settings": lab_env.load_settings(),
                        "defaults": lab_env.composite_defaults()})
        elif path == "/api/models":
            self._json({"models": lab_models.status(),
                        "installed_default": lab_models.resolve_default()})
        elif path == "/api/llm":
            self._json(llm_enhance.status())
        elif path == "/api/cost":
            q = lambda k, d: query.get(k, [d])[0]  # noqa: E731
            try:
                seconds = float(q("seconds", "60"))
                retakes = int(q("retakes", "1"))
            except ValueError:
                seconds, retakes = 60.0, 1
            self._json(cost.estimate(seconds, q("engine", "kenburns"),
                                     retakes, q("voice", "sapi")))
        elif path == "/api/keyframes":
            proj = self._project(query)
            kdir = proj / "assets" / "keyframes"
            files = []
            if kdir.exists():
                for f in sorted(kdir.iterdir()):
                    if f.is_file() and f.suffix.lower() in kenburns.IMAGE_EXTS:
                        files.append({"name": f.name, "shot": f.stem,
                                      "size": f.stat().st_size})
            self._json({"keyframes": files, "dir": str(kdir)})
        elif path.startswith("/api/run/"):
            name = path.rsplit("/", 1)[-1]
            try:
                proj = self._project(query)
                if name == "composite":
                    d = lab_env.composite_defaults()
                    engine = query.get("engine", [d["engine"]])[0]
                    fps = int(query.get("fps", [d["fps"]])[0])
                    width = int(query.get("width", [d["width"]])[0])
                    height = int(query.get("height", [d["height"]])[0])
                    steps = int(query.get("steps", ["20"])[0])
                    max_frames = int(query.get("max_frames", ["25"])[0])
                    reuse = query.get("reuse", ["1"])[0] not in ("0", "false")
                    transition = query.get("transition", ["none"])[0]
                    try:
                        xfade = float(query.get("xfade", ["0.5"])[0])
                    except ValueError:
                        xfade = 0.5
                    subtitles = query.get("subtitles", ["0"])[0] in ("1", "true")
                    self._json(composite.run(proj, engine, fps, width, height,
                                             reuse=reuse, steps=steps,
                                             max_frames=max_frames,
                                             transition=transition, xfade=xfade,
                                             subtitles=subtitles))
                else:
                    self._json(run_stage(name, proj))
            except Exception as e:  # noqa: BLE001
                self._json({"status": "error", "stage": name, "error": str(e)}, 500)
        elif path == "/api/file/script":
            script = self._project(query) / "script" / "script.md"
            self._file(script, "text/plain; charset=utf-8")
        elif path.startswith("/api/file/"):
            name = path.rsplit("/", 1)[-1]
            if name not in ALLOWED_FILES:
                self._json({"error": "not allowed"}, 403)
                return
            self._file(self._project(query) / name, "text/plain; charset=utf-8")
        elif path == "/api/media/final":
            final = self._project(query) / "output" / "final.mp4"
            if not final.exists():
                self._json({"error": "no final.mp4 yet"}, 404)
                return
            body = final.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path in ("/", "/index.html"):
            self._file(STATIC / "index.html", "text/html; charset=utf-8")
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(body.decode("utf-8"))
        except Exception:
            data = {}
        if parsed.path == "/api/project/new":
            name = Path(str(data.get("name", "demo"))).name
            if not name:
                self._json({"error": "name required"}, 400)
                return
            proj = PROJECTS / name
            for sub in ["script", "output", "clips", "prompts", "audio/voice",
                        "assets/keyframes", "assets/footage"]:
                (proj / sub).mkdir(parents=True, exist_ok=True)
            self._json({"status": "ok", "project": name})
        elif parsed.path == "/api/project/delete":
            name = Path(str(data.get("name", ""))).name
            if not name:
                self._json({"error": "name required"}, 400)
                return
            proj = PROJECTS / name
            if not proj.exists():
                self._json({"status": "ok", "project": name, "removed": False})
                return
            if proj.resolve().parent != PROJECTS.resolve():
                self._json({"error": "refusing to delete outside projects dir"}, 403)
                return
            shutil.rmtree(proj, ignore_errors=True)
            self._json({"status": "ok", "project": name, "removed": not proj.exists()})
        elif parsed.path == "/api/script/import":
            content = data.get("content")
            if not content or not content.strip():
                self._json({"error": "empty script content"}, 400)
                return
            if len(content.encode("utf-8")) > MAX_SCRIPT_BYTES:
                self._json({"error": "script too large (max 2MB)"}, 413)
                return
            proj = self._project(query)
            script = proj / "script" / "script.md"
            script.parent.mkdir(parents=True, exist_ok=True)
            script.write_text(content, encoding="utf-8")
            try:
                res = import_script.run(proj, script)
                res["status"] = "ok"
                self._json(res)
            except Exception as e:  # noqa: BLE001
                self._json({"status": "error", "error": str(e)}, 500)
        elif parsed.path == "/api/storyboard/rebuild":
            proj = self._project(query)
            mode = str(data.get("mode", "auto"))
            try:
                self._json(storyboard.run(proj, mode=mode))
            except Exception as e:  # noqa: BLE001
                self._json({"status": "error", "error": str(e)}, 500)
        elif parsed.path == "/api/prompt/regenerate":
            proj = self._project(query)
            target = str(data.get("shot", "")).strip()
            manifest = _load_manifest(proj)
            style = promptgen.load_style(proj, manifest)
            if target:
                # Regenerate one shot's prompt from its row.
                shots = list_shots(proj)
                row = next((s for s in shots if s["shot"] == target), None)
                if not row:
                    self._json({"error": f"no shot {target}"}, 404)
                    return
                pf = proj / "prompts" / f"{target}.txt"
                pf.write_text(promptgen.generate(row, manifest, style), encoding="utf-8")
                self._json({"status": "ok", "shot": target,
                            "prompt": pf.read_text(encoding="utf-8")})
            else:
                # Regenerate all shots from current shot_list rows.
                proj2 = self._project(query)
                count = 0
                for row in list_shots(proj2):
                    pf = proj2 / "prompts" / f"{row['shot']}.txt"
                    pf.write_text(promptgen.generate(row, manifest, style), encoding="utf-8")
                    count += 1
                self._json({"status": "ok", "regenerated": count})
        elif parsed.path == "/api/prompt/preview":
            # Practice: enhance/preview a prompt WITHOUT writing it to disk.
            proj = self._project(query)
            target = str(data.get("shot", "")).strip()
            text = str(data.get("prompt", "")).strip()
            if not text:
                self._json({"error": "prompt required"}, 400)
                return
            shots = list_shots(proj)
            row = next((s for s in shots if s["shot"] == target), None)
            manifest = _load_manifest(proj)
            style = promptgen.load_style(proj, manifest)
            res = promptgen.optimize(text, row, style, use_llm=bool(data.get("use_llm")))
            res["shot"] = target
            self._json(res)
        elif parsed.path == "/api/prompt/optimize":
            proj = self._project(query)
            target = str(data.get("shot", "")).strip()
            text = str(data.get("prompt", "")).strip()
            if not target or not text:
                self._json({"error": "shot and prompt required"}, 400)
                return
            shots = list_shots(proj)
            row = next((s for s in shots if s["shot"] == target), None)
            manifest = _load_manifest(proj)
            style = promptgen.load_style(proj, manifest)
            res = promptgen.optimize(text, row, style, use_llm=bool(data.get("use_llm")))
            if not res.get("ok"):
                self._json({"status": "error", "error": res.get("error")}, 400)
                return
            pf = proj / "prompts" / f"{target}.txt"
            pf.write_text(res["prompt"], encoding="utf-8")
            self._json({"status": "ok", "shot": target, "prompt": res["prompt"],
                        "changed": res["changed"], "engine": res.get("engine", "rules")})
        elif parsed.path == "/api/prompt/save":
            proj = self._project(query)
            target = str(data.get("shot", "")).strip()
            text = str(data.get("prompt", "")).strip()
            if not target or not text:
                self._json({"error": "shot and prompt required"}, 400)
                return
            pf = proj / "prompts" / f"{target}.txt"
            pf.write_text(text, encoding="utf-8")
            self._json({"status": "ok", "shot": target, "saved": True})
        elif parsed.path == "/api/style/save":
            proj = self._project(query)
            clean = promptgen.save_style(proj, data.get("style", {}))
            # Re-sync every shot prompt's character:/consistent: layers to the
            # new anchors so all shots stay coherent (批量统一).
            manifest = _load_manifest(proj)
            style = promptgen.load_style(proj, manifest)
            count = 0
            for row in list_shots(proj):
                pf = proj / "prompts" / f"{row['shot']}.txt"
                if pf.exists():
                    res = promptgen.optimize(pf.read_text(encoding="utf-8"), row, style)
                    if res.get("ok"):
                        pf.write_text(res["prompt"], encoding="utf-8")
                        count += 1
            self._json({"status": "ok", "style": style, "resynced": count})
        elif parsed.path == "/api/settings":
            merged = lab_env.save_settings(data if isinstance(data, dict) else {})
            self._json({"status": "ok", "settings": merged,
                        "defaults": lab_env.composite_defaults()})
        elif parsed.path == "/api/models/download":
            name = str(data.get("name", "")).strip()
            if not name:
                self._json({"error": "name required"}, 400)
                return
            res = lab_models.download(name)
            self._json(res, 200 if res.get("status") == "ok" else 500)
        elif parsed.path == "/api/keyframes/upload":
            proj = self._project(query)
            shot = Path(str(data.get("shot", ""))).name
            data_url = str(data.get("data_url", ""))
            if not shot or "," not in data_url:
                self._json({"error": "shot and data_url required"}, 400)
                return
            header, b64 = data_url.split(",", 1)
            ext = ".png"
            for cand in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
                if cand in header.lower():
                    ext = cand
                    break
            try:
                raw = base64.b64decode(b64)
            except Exception:
                self._json({"error": "bad base64"}, 400)
                return
            if len(raw) > 8 * 1024 * 1024:
                self._json({"error": "image too large (max 8MB)"}, 413)
                return
            kdir = proj / "assets" / "keyframes"
            kdir.mkdir(parents=True, exist_ok=True)
            out = kdir / f"{shot}{ext}"
            out.write_bytes(raw)
            self._json({"status": "ok", "shot": shot, "file": out.name,
                        "size": len(raw)})
        elif parsed.path == "/api/keyframes/delete":
            proj = self._project(query)
            name = Path(str(data.get("name", ""))).name
            target = proj / "assets" / "keyframes" / name
            if not name or not target.exists():
                self._json({"status": "ok", "removed": False})
                return
            if target.suffix.lower() not in kenburns.IMAGE_EXTS:
                self._json({"error": "not an image"}, 400)
                return
            target.unlink()
            self._json({"status": "ok", "removed": True})
        elif parsed.path == "/api/pipeline/import":
            name = Path(str(data.get("name", ""))).name
            content = str(data.get("content", "")).strip()
            if not name:
                self._json({"error": "name required"}, 400)
                return
            if not content:
                self._json({"error": "empty script content"}, 400)
                return
            if len(content.encode("utf-8")) > MAX_SCRIPT_BYTES:
                self._json({"error": "script too large (max 2MB)"}, 413)
                return
            proj = PROJECTS / name
            for sub in ["script", "output", "clips", "prompts", "audio/voice",
                        "assets/keyframes", "assets/footage"]:
                (proj / sub).mkdir(parents=True, exist_ok=True)
            script = proj / "script" / "script.md"
            script.write_text(content, encoding="utf-8")
            try:
                imp = import_script.run(proj, script)
                sb = storyboard.run(proj, mode="auto")
                self._json({"status": "ok", "project": name,
                            "title": imp.get("title", ""),
                            "scenes": imp.get("scene_count", 0),
                            "shots": sb.get("shots", 0),
                            "total_duration_s": sb.get("total_duration_s", 0)})
            except Exception as e:  # noqa: BLE001
                self._json({"status": "error", "error": str(e)}, 500)
        else:
            self._json({"error": "not found"}, 404)


def serve(port: int = 8765):
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"本地 AI 视频实验室 · 管理台: http://127.0.0.1:{port}")
    print("按 Ctrl+C 停止")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    serve(args.port)
