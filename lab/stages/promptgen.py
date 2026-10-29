"""Seedance prompt generation & optimization (rules-based, no LLM needed).

This is the "自动生成 Seedance 提示词并优化" capability. It assembles a
structured, cinematic prompt for each shot from layers
(subject+action / character / environment / lighting / camera / style /
consistent / format / negative), in a Seedance 2.0-compatible style
(referenced from Emily2040/seedance-2.0 and dexhunter/seedance2-skill).

**Cross-scene consistency**: the project holds a "story style" anchor set
(story_style.json) — character, costume, props, setting, palette — extracted
from the script and editable in the console. Every shot prompt gets the SAME
`character:` and `consistent:` layers, so scenes rendered independently by
Seedance still share the same person, costume and props (prevents the
"each scene looks different / incoherent" problem).

Rules-based so it works offline on the 4GB CPU machine; the `text engine` knob
in config.yaml (template | llm) can later swap in an LLM for semantic rewrite
without changing the prompt file contract.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

# ---- Seedance 2.0 style knobs -------------------------------------------------
DEFAULT_ASPECT = "16:9"
DEFAULT_SECONDS = 5
DEFAULT_STYLE = "cinematic, film grain, shallow depth of field, 35mm anamorphic look"
DEFAULT_PALETTE = "warm cinematic palette, rich contrast, natural color grading"

# Layer order (fixed for deterministic prompts + optimisation).
LAYER_ORDER = ("subject", "action", "character", "environment", "lighting",
               "camera", "style", "consistent", "format", "negative")
_LAYER_RE = re.compile(
    r"^(subject|action|character|environment|lighting|camera|style|consistent|format|negative)\s*:\s*(.*)$",
    re.IGNORECASE,
)

# Framing / camera vocabulary (Seedance-recognised English terms).
SHOT_SIZE_FRAMING = {
    "特写": "extreme close-up",
    "近景": "close-up",
    "中景": "medium shot",
    "中近景": "medium close-up",
    "全景": "wide shot",
    "远景": "extreme wide shot",
    "大特写": "macro shot",
}
CAMERA_MOVE = {
    "缓慢推近": "slow push-in",
    "推近": "push-in",
    "缓慢拉远": "slow pull-back",
    "拉远": "pull-back",
    "横移": "lateral tracking shot",
    "环绕": "orbit around subject",
    "固定": "static locked-off shot",
    "手持": "handheld, slight natural sway",
    "跟随": "following subject, tracking",
    "上升": "crane rise",
}
LIGHT_PRESETS = {
    "暖色灯光": "warm lantern key light, soft shadows, gentle rim light",
    "冷色灯光": "cool neon fill, hard shadows, high contrast",
    "自然光": "soft natural daylight, diffused, airy",
    "夜景": "night scene, warm practical lights, deep blue ambient",
    "逆光": "backlit silhouette, strong rim light, atmospheric haze",
    "霓虹": "neon signage glow, magenta and cyan reflections",
    "暗调": "low-key lighting, deep shadows, single source",
}

# Negative constraints: Seedance/volcengine render well without these artifacts.
NEGATIVE = (
    "no text, no watermark, no logo, no caption, no subtitle, "
    "no extra fingers, no distorted hands, no warped face, "
    "no flicker, no jitter, no morphing, no duplicate characters, "
    "no style drift, no costume change, no character change"
)

# Verb cues -> likely beat / function (used to split one scene into shots).
_ACTION_BEATS = [
    (re.compile(r"打开|开扇|展开|亮相|登场"), "动作开启"),
    (re.compile(r"合上|收扇|定格|定姿|谢幕|落幕|收势"), "收束定格"),
    (re.compile(r"蒙太奇|闪过|快切|快速|闪回|穿插"), "节奏蒙太奇"),
    (re.compile(r"跨出|走出|离开|转身|奔跑|冲|跃"), "转场运动"),
    (re.compile(r"特写|细节|近景|蒸汽|水滴|纹理|眼神|手部"), "细节特写"),
]

# ---- Story style (cross-scene consistency anchors) ---------------------------
DEFAULT_STYLE_FILE = "story_style.json"
_STOPWORDS = set(
    "一个 一些 这个 那个 这些 那些 我们 你们 他们 我们 我 你 他 她 它 的 了 着 在 是 有 和 与 就 都 很 也 又 再 把 被 让 向 从 对 里 中 上 下 到 去 来 说 看 走 站 坐 起 开 合 关 打 拿 放 穿 戴 披 执 持 着 那 这 只 件 个 位 名 场 幕 里 边 前 后 间 时 候".split()
)
_SETTING_HINTS = (
    "茶馆", "茶楼", "舞台", "剧场", "城市", "街道", "霓虹", "老宅", "川西",
    "屋檐", "山", "江", "桥", "教室", "医院", "雨夜", "雨", "夜", "巷", "码头",
    "广场", "教室", "工厂", "森林", "海边", "沙漠", "车站", "酒吧", "书店",
)
_PROP_HINTS = (
    "折扇", "扇子", "盖碗", "茶碗", "茶杯", "戏服", "长衫", "旗袍", "剑", "刀",
    "枪", "伞", "灯笼", "面具", "脸谱", "琵琶", "笛", "书", "信", "戒指", "项链",
    "眼镜", "帽子", "围巾", "烟斗", "相机", "手机", "吉他", "鼓", "锣", "琴",
)


def detect_beats(action: str) -> list[str]:
    """Return ordered beat labels a scene's action suggests (for shot splitting)."""
    beats: list[str] = []
    for rx, label in _ACTION_BEATS:
        if rx.search(action):
            beats.append(label)
    if not beats:
        beats.append("叙事")
    seen: list[str] = []
    for b in beats:
        if b not in seen:
            seen.append(b)
    return seen


def extract_style(manifest: dict | None) -> dict:
    """Heuristically extract a cross-scene consistency anchor set from the script.

    No LLM needed: finds the recurring protagonist name, props, setting and a
    palette from the whole script. The console lets the user refine these; they
    are injected into EVERY shot prompt as character:/consistent: layers.
    """
    manifest = manifest or {}
    scenes = manifest.get("scenes", [])
    texts = [str(manifest.get("title", "")), str(manifest.get("logline", ""))]
    for sc in scenes:
        texts.append(str(sc.get("title", "")))
        texts.extend(str(l) for l in sc.get("lines", []))
    full = "\n".join(texts)

    # 1) Protagonist name: token immediately before a "doing" verb, most frequent.
    #    Filter out tokens containing setting/prop/stop chars so "雨夜穿梭" is
    #    NOT mistaken for a name; a real protagonist recurs across scenes.
    name_counter: Counter[str] = Counter()
    verb_re = re.compile(
        r"([\u4e00-\u9fa5]{2,3})(?=穿|戴|拿|坐|站|走|跨|跨上|戴上|拿起|打开|合上|"
        r"看|说|转身|推|回|停|望|举|递给|交给|接过|奔向|骑上|按下|按下|戴上|换上)"
    )
    bad_chars = set("".join(_SETTING_HINTS) + "".join(_PROP_HINTS) + "的着在是和与就都很也又再")
    for t in texts:
        for m in verb_re.finditer(t):
            tok = m.group(1)
            if tok in _STOPWORDS or len(tok) < 2:
                continue
            if any(ch in bad_chars for ch in tok):
                continue
            name_counter[tok] += 1
    # Prefer a token that recurs (>=2 scenes) and looks like a name (小/阿/老/姓).
    named = [(tok, n) for tok, n in name_counter.items() if tok[0] in "小阿老"]
    if named:
        character = max(named, key=lambda x: x[1])[0]
    elif name_counter:
        character = name_counter.most_common(1)[0][0]
    else:
        character = ""

    # 2) Props: explicit prop words present in the script.
    props = [h for h in _PROP_HINTS if h in full]
    props = props[:6]

    # 3) Setting tokens discovered from the script (NOT hard-coded per demo).
    settings = []
    for h in _SETTING_HINTS:
        if h in full and h not in settings:
            settings.append(h)
    if "雨" in full and "雨夜" not in settings:
        settings.append("雨夜")

    # 4) Palette: colour hints in the script.
    palette = DEFAULT_PALETTE
    if any(k in full for k in ("戏服", "红黑", "红色", "大红", "金")):
        palette = "warm red, gold and deep black palette, rich contrast"
    elif any(k in full for k in ("霓虹", "灯", "夜")):
        palette = "neon magenta and cyan palette, high contrast"

    style = {
        "character": character or "a lone protagonist",
        "costume": "、".join([p for p in props if p in ("戏服", "长衫", "旗袍")][:2]) or "consistent costume",
        "props": "、".join(props) or "consistent props",
        "setting": "、".join(settings) or "consistent setting",
        "palette": palette,
    }
    return style


def style_path(project: Path) -> Path:
    return Path(project) / DEFAULT_STYLE_FILE


def load_style(project: Path, manifest: dict | None = None) -> dict:
    """Load story_style.json; auto-extract + persist a default if missing."""
    path = style_path(project)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    style = extract_style(manifest)
    try:
        path.write_text(json.dumps(style, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    return style


def save_style(project: Path, style: dict) -> dict:
    path = style_path(project)
    clean = {k: str(v).strip() for k, v in style.items() if k in
             ("character", "costume", "props", "setting", "palette")}
    path.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
    return clean


def consistency_layers(style: dict) -> tuple[str, str]:
    """Build character: and consistent: lines from the style anchor set."""
    s = style or {}
    char = str(s.get("character", "")).strip() or "a lone protagonist"
    costume = str(s.get("costume", "")).strip()
    props = str(s.get("props", "")).strip()
    setting = str(s.get("setting", "")).strip()
    palette = str(s.get("palette", "")).strip() or DEFAULT_PALETTE
    char_line = f"character: {char}" + (f", wearing {costume}" if costume and costume != "consistent costume" else "")
    parts = ["same character throughout"]
    if costume and costume != "consistent costume":
        parts.append(f"same costume ({costume})")
    if props and props != "consistent props":
        parts.append(f"same props ({props})")
    if setting:
        parts.append(f"same setting ({setting})")
    parts.append(f"same palette ({palette})")
    cons_line = "consistent: " + ", ".join(parts) + " — no style drift between shots"
    return char_line, cons_line


# ---- Environment (dynamic, not hard-coded per demo) --------------------------
def _env_from_texts(text: str, style: dict | None = None) -> str:
    found = [h for h in _SETTING_HINTS if h in text]
    # Dedup + normalise 雨夜
    uniq = []
    for h in found:
        if h == "雨" and "雨夜" in uniq:
            continue
        if h not in uniq:
            uniq.append(h)
    if not uniq:
        return "cinematic environment, atmospheric depth, detailed set design"
    return f"set in {', '.join(uniq)} atmosphere, detailed, lived-in, atmospheric depth"


def _light_from_text(text: str) -> str:
    if any(k in text for k in ("霓虹", "夜", "夜景", "暗")):
        return LIGHT_PRESETS["夜景"]
    if "雨" in text:
        return LIGHT_PRESETS["暖色灯光"]
    return LIGHT_PRESETS["暖色灯光"]


def generate(shot: dict, manifest: dict | None = None, style: dict | None = None) -> str:
    """Assemble a full Seedance prompt for one shot row (with consistency anchors)."""
    manifest = manifest or {}
    action = str(shot.get("action", "")).strip()
    scene_title = str(shot.get("scene", "")).strip()
    framing = SHOT_SIZE_FRAMING.get(str(shot.get("shot_size", "")), "medium shot")
    move = CAMERA_MOVE.get(str(shot.get("camera", "")), "slow push-in")
    try:
        seconds = float(shot.get("duration_s", DEFAULT_SECONDS) or DEFAULT_SECONDS)
    except (TypeError, ValueError):
        seconds = float(DEFAULT_SECONDS)

    # Scene + global text for environment/light detection.
    scene_text = scene_title + " " + action
    global_text = scene_text + " " + str(manifest.get("logline", "")) + " " + str(manifest.get("title", ""))
    light = LIGHT_PRESETS.get(str(shot.get("light", "")),
                              _light_from_text(global_text))
    env = _env_from_texts(global_text, style)

    subject = re.split(r"[，。；,]|[,.;]", action)[0].strip() or scene_title or "a lone figure"
    char_line, cons_line = consistency_layers(style or {})

    lines = [
        f"subject: {subject}",
        f"action: {action}",
        char_line,
        f"environment: {env}",
        f"lighting: {light}",
        f"camera: {framing}, {move}",
        f"style: {DEFAULT_STYLE}",
        cons_line,
        f"format: {DEFAULT_ASPECT}, {seconds:.1f} seconds, consistent character and costume",
        f"negative: {NEGATIVE}",
    ]
    return "\n".join(lines)


# ---- Optimization -------------------------------------------------------------
def optimize(text: str, shot: dict | None = None, style: dict | None = None) -> dict:
    """Enhance / normalise a prompt: fill missing layers, dedup, cap length."""
    orig = (text or "").strip()
    if not orig:
        return {"ok": False, "error": "empty prompt"}

    layer_map: dict[str, str] = {}
    body: list[str] = []
    for ln in orig.splitlines():
        s = ln.strip()
        m = _LAYER_RE.match(s)
        if m:
            key = m.group(1).lower()
            val = m.group(2).strip()
            if key not in layer_map:
                layer_map[key] = val
            continue
        if s:
            body.append(s)

    changed: list[str] = []
    if body and "action" not in layer_map:
        layer_map["action"] = " ".join(body)
        changed.append("fold free text -> action")
    if "action" not in layer_map:
        layer_map["action"] = "a cinematic scene"
        changed.append("add action")

    char_line, cons_line = consistency_layers(style or {})
    defaults = {
        "subject": (shot.get("action", "a lone figure") if shot else "a lone figure"),
        "character": char_line.split(":", 1)[1].strip(),
        "environment": "cinematic environment, atmospheric depth",
        "lighting": (LIGHT_PRESETS.get(shot.get("light", ""), LIGHT_PRESETS["暖色灯光"])
                     if shot else LIGHT_PRESETS["暖色灯光"]),
        "camera": "medium shot, slow push-in",
        "style": DEFAULT_STYLE,
        "consistent": cons_line.split(":", 1)[1].strip(),
        "format": f"{DEFAULT_ASPECT}, {DEFAULT_SECONDS} seconds, consistent character and costume",
        "negative": NEGATIVE,
    }
    for k in LAYER_ORDER:
        if k not in layer_map:
            layer_map[k] = defaults.get(k, "")
            changed.append(f"add {k}")

    # Rebuild character:/consistent: from the style anchors if they drifted
    # (i.e. someone edited them inconsistently across shots) — keeps coherence.
    if style:
        new_char, new_cons = consistency_layers(style)
        if layer_map["character"] != new_char.split(":", 1)[1].strip():
            layer_map["character"] = new_char.split(":", 1)[1].strip()
            changed.append("sync character (style)")
        if layer_map["consistent"] != new_cons.split(":", 1)[1].strip():
            layer_map["consistent"] = new_cons.split(":", 1)[1].strip()
            changed.append("sync consistent (style)")

    ordered = [layer_map[k] for k in LAYER_ORDER]
    return {"ok": True, "prompt": "\n".join(f"{k}: {v}" for k, v in zip(LAYER_ORDER, ordered)),
            "changed": changed}


if __name__ == "__main__":
    import sys

    demo = {
        "shot": "S01", "shot_size": "中景", "camera": "缓慢推近",
        "action": "小禾打开红色折扇，眼神自信看向镜头",
        "light": "暖色灯光", "scene": "第一场 · 开扇亮相",
    }
    if len(sys.argv) > 1 and Path(sys.argv[1]).exists():
        res = optimize(Path(sys.argv[1]).read_text(encoding="utf-8"), demo)
    else:
        res = {"ok": True, "prompt": generate(demo), "changed": []}
    print(json.dumps(res, ensure_ascii=False, indent=2))
