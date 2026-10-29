# 30 秒川味变体 Demo：一碗茶，慢慢摆

## 状态

- 本地可播放成片：**已完成**
- 成片：`output/sichuan_teahouse_16x9_v01.mp4`
- 时长：30.00 秒
- 画面：1280×720，30fps，H.264
- 音频：AAC，44.1kHz，立体声
- 角色：小禾（原创川剧变脸学徒）
- 场景：雨夜老茶馆、盖碗茶、川剧小舞台、火锅、雨巷
- 明确避开：熊猫 Rap 本体、原案例角色/歌词/品牌/活动标识

## 这条 Demo 证明了什么

用同一条流水线，换一个题材，仍然能在 30 秒内完成：

```text
AI 写词 → Suno 出歌 → ComfyUI + Seedance 出 4–5 个 5 秒镜头 → 剪映拼装 + 字幕 + 调色
```

当前版本是**离线可播放版**；正式路线改为**免费官方路线**：

| 环节 | 当前实现 | 说明 |
|---|---|---|
| AI 写词 | 原创歌词 + Suno 提示词 | 已准备 `06_suno_prompt.md`；后续用 Doubao-Seed-Evolving 重写 |
| Suno 出歌 | 程序化川味 beat + SAPI 念白占位 | 有账号后用 Suno 每日免费积分替换 `audio/` |
| 即梦/Seedance | 提示词 + 官方网页版入口 | 5 秒镜头用免费积分跑；见 `08_free_route.md` |
| ComfyUI | 本地备用 | 只用于练习、首帧图、离线兜底 |
| 剪映/CapCut | 完成拼装/字幕/调色 | 另生成 CapCut 草稿，方便人工精修 |

## 文件

```text
demo_sichuan/
  00_concept.md          概念卡
  01_lyrics.md           原创歌词 + 念白时间码
  02_beat_sheet.csv      92 BPM 节奏表
  03_shot_list.csv       6 个 5 秒镜头
  04_asset_passport.md   角色/场景一致性护照
  05_prompts/            ComfyUI / Seedance 提示词
  06_suno_prompt.md      Suno 风格 + 歌词 + 剪辑建议
  07_seedance_api.md     Seedance 流程与 API 说明
  tools/
    SichuanRenderer.cs   矢量画面/字幕/封面渲染器
    SichuanBeatGenerator.cs  川味 beat 合成器
    make_voice.ps1       SAPI 念白
    render.ps1           一键重建
    seedance_api.py      Seedance 占位脚本
  output/
    sichuan_teahouse_16x9_v01.mp4
    cover.png
    contact_sheet.jpg
```

## 一键重建

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "demo_sichuan\tools\render.ps1" -Root "demo_sichuan"
```

依赖：

- `.NET Framework` 自带的 `csc.exe`（脚本自动从 `$env:WINDIR` 查找）
- `ffmpeg`（优先 CapCut 自带，其次 PATH，也可用 `imageio-ffmpeg` 提供的二进制）
- Windows 中文语音 `Microsoft Huihui Desktop`

## 镜头结构

| 镜头 | 时间 | 内容 | 字幕 |
|---|---|---|---|
| S01 | 0–5s | 雨夜老茶馆、红灯笼、盖碗茶蒸汽 | 雨点敲青瓦，盖碗泡时光 |
| S02 | 5–10s | 揭盖碗、茶汤、雨窗散景 | 莫慌嘛，龙门阵慢慢摆 |
| S03 | 10–15s | 小禾变脸、红黑金脸谱、观众剪影 | 脸一换，红堂堂，满堂彩 |
| S04 | 15–20s | 火锅红汤、辣椒花椒、毛肚 | 火锅一滚，椒麻烫心肠 |
| S05 | 20–25s | 雨巷红灯笼、小禾和伙伴同行 | 巴适得板，日子有腔调 |
| S06 | 25–30s | 标题卡 | 一碗茶，慢慢摆 |

## 下一步替换真实云端素材

1. 用 Suno 生成 30 秒版本，导出 `audio/suno_v01.wav`。
2. 用 ComfyUI 生成 5 张关键帧，放 `assets/keyframes/`。
3. 用 Seedance 生成 5 段 5 秒视频，放 `assets/seedance/`。
4. 在 CapCut 里替换对应镜头，保留字幕和时间码。
5. 重新导出，跑 QC。

## 约束

- 不使用原案例的视频、音频、歌词、截图、品牌/活动标识、聊天原话或隐私信息。
