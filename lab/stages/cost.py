"""Cost estimator (practice tool, offline arithmetic only).

Gives a rough CNY estimate for a video of a given length and engine. Prices are
deliberately conservative ranges from the docs, not live quotes. Useful for the
"practice workbench" and for planning before spending on a cloud engine.
"""
from __future__ import annotations

import math

# Per-shot (5s) unit cost in CNY, with a low/high band.
# key -> (label, low_per_shot, high_per_shot, note)
ENGINES: dict[str, tuple[str, float, float, str]] = {
    "kenburns": ("关键帧动效", 0.0, 0.0, "纯 FFmpeg，无模型费用"),
    "placeholder": ("占位色块", 0.0, 0.0, "纯 FFmpeg"),
    "footage": ("实拍素材", 0.0, 0.0, "已有授权素材，无生成费用"),
    "wan_local": ("本地 Wan", 0.05, 0.2, "仅电费/时间，CPU 很慢"),
    "seedance": ("云端 Seedance", 8.0, 22.0, "按方舟实际计费为准"),
}

VOICE = {
    "sapi": ("本地 SAPI 念白", 0.0),
    "suno": ("Suno 订阅/积分", 0.0),  # 订阅制，按计划摊销
    "none": ("无声音", 0.0),
}

SHOT_SECONDS = 5.0


def estimate(seconds: float, engine: str = "kenburns", retakes: int = 1,
             voice: str = "sapi") -> dict:
    """Estimate cost for a video of `seconds` length."""
    try:
        seconds = max(1.0, float(seconds))
    except (TypeError, ValueError):
        seconds = 60.0
    retakes = max(1, int(retakes or 1))
    key = engine if engine in ENGINES else "kenburns"
    label, low, high, note = ENGINES[key]
    shots = math.ceil(seconds / SHOT_SECONDS)
    # Retakes multiply only the generation cost, not editing.
    low_total = shots * low * retakes
    high_total = shots * high * retakes
    voice_label, voice_cost = VOICE.get(voice, VOICE["sapi"])
    return {
        "seconds": seconds,
        "shots": shots,
        "engine": key,
        "engine_label": label,
        "retakes": retakes,
        "voice": voice,
        "voice_label": voice_label,
        "currency": "CNY",
        "low": round(low_total + voice_cost, 2),
        "high": round(high_total + voice_cost, 2),
        "note": note,
    }
