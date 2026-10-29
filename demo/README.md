# 《晚到也算到》— 24 秒本地离线 Demo

这是一个**完整闭环**的 AI 音乐短片课程 Demo，按 2 天工作坊的交付标准制作：

- 时长：24 秒
- 角色：1 个（咖啡师「小满」）
- 场景：2 个（清晨咖啡馆内景 / 雨夜街角外景）
- 镜头：8 个
- 画幅：16:9，1280×720，30fps
- 成片：`output/street_corner_cafe_16x9_v01.mp4`
- 封面：`output/cover.png`
- 已测试输出：24.00s / 1280×720 / 30fps / H.264 + AAC / 9.79 MB
- QC：`edit/qc_report.md`（已通过）

## 已生成的文件

| 文件 | 说明 |
|---|---|
| `output/street_corner_cafe_16x9_v01.mp4` | 24 秒成片 |
| `output/cover.png` | 封面 |
| `output/contact_sheet.jpg` | 8 镜头接触表 |
| `output/waveform.png` | 混音波形 |
| `audio/beat.wav` | 24 秒程序合成 beat |
| `audio/voice/line01.wav`–`line07.wav` | 7 句 SAPI 念白 |
| `audio/mix.wav` | 24 秒混音 |
| `assets/characters/xiaoman_sheet.png` | 角色定妆照 |
| `assets/scenes/cafe_dawn.png` | 咖啡馆场景图 |
| `assets/scenes/street_rain.png` | 雨夜街角场景图 |
| `assets/props/cup_sleeve.png` | 杯套道具图 |

## 这个 Demo 是什么

| 层级 | 本 Demo 的做法 | 正式生产时替换为 |
|---|---|---|
| 歌词 | 原创 8 句，Hook / Verse / Chorus / CTA | 同一套歌词模板 |
| 音乐 | 本地合成的 90 BPM lo-fi beat | Suno 生成的完整歌曲 + 分轨 |
| 人声 | Windows SAPI 中文念白 | Suno 人声或真人演唱 |
| 画面 | 原创矢量动态分镜（animatic） | Seedance 图生视频 / 首尾帧 |
| 剪辑 | 脚本渲染 + ffmpeg 合成 | 剪映 Skill 粗剪 + 精剪 |
| 资产 | 程序绘制的角色/场景/道具 | 角色定妆照 + 场景参考图 |

> 这不是"假装 AI 生成"的成片。它明确是一个**离线动态分镜 Demo**：用来验证歌词、节拍、镜头、字幕、混音、导出、QC 的完整流程。所有提示词和资产护照已经写好，拿到 Seedance / Suno 账号后可以直接替换对应层。

## 为什么做离线版

当前机器没有 WorkBuddy、ComfyUI、Seedance / Suno 凭证，也没有 Python / Node / ffmpeg 的独立安装。  
但机器上有：

- Windows 11 + 64GB RAM
- .NET Framework 4.8 / csc
- CapCut 9.6（自带可用的 ffmpeg 与 H.264/AAC 编码器）
- VLC 3.0（备用转码）
- Edge（可用于 HTML 预览）
- SAPI 中文语音 `Microsoft Huihui Desktop`

因此可以完成一个**不依赖云端**的最小闭环，并且不下载任何模型或素材。

## 目录

```
demo/
├─ 00_concept.md
├─ 01_lyrics.md
├─ 02_beat_sheet.csv
├─ 03_shot_list.csv
├─ 04_asset_passport.md
├─ 05_prompts/              # 8 个镜头提示词（可直接给 Seedance）
├─ assets/                  # 程序生成的角色/场景/道具图
├─ audio/                   # beat / voice / mix
├─ edit/
│  ├─ edl.csv
│  └─ qc_report.md
├─ logs/
│  ├─ cost_log.csv
│  └─ time_log.csv
├─ output/
│  ├─ frames/               # 渲染帧（可删除，重新生成）
│  ├─ cover.png
│  ├─ contact_sheet.jpg
│  ├─ waveform.png
│  └─ street_corner_cafe_16x9_v01.mp4
└─ tools/
   ├─ DemoRenderer.cs
   ├─ BeatGenerator.cs
   ├─ render.ps1
   └─ make_voice.ps1
```

## 重新生成

在 Windows PowerShell 中：

```powershell
cd demo
powershell -ExecutionPolicy Bypass -File .\tools\render.ps1
```

脚本会：

1. 用 `csc.exe` 编译 `DemoRenderer.cs`
2. 渲染 720 帧 JPEG
3. 生成 24 秒 beat
4. 用 SAPI 生成 7 句念白
5. 用 CapCut 自带 ffmpeg 混音
6. 用 `h264_mf` + AAC 导出 MP4
7. 生成封面、角色/场景/道具资产

## 替换为正式 AI 生产

1. 把 `04_asset_passport.md` 的角色/场景段落**逐字复制**到每个 Seedance 提示词。
2. 按 `05_prompts/S01.txt`–`S08.txt` 生成 8 个镜头，每个 2 take。
3. 用 Suno 生成 90 BPM、24 秒左右的歌，导出 vocal + instrumental。
4. 按 `02_beat_sheet.csv` 把镜头对齐到小节。
5. 用剪映替换 `output/frames` 对应的占位画面，保留 `edit/edl.csv` 的节奏。
6. 按 `edit/qc_report.md` 做 QC。

## 版权与合规

- 故事、歌词、角色、画面均为本项目原创/程序生成，不使用原案例的视频、音频、歌词、截图、品牌或活动标识。
- 音乐为程序合成的简单 beat，不含第三方采样。
- 人声由本机 SAPI 生成。
- 本 Demo 仅用于课程演示，不构成对任何品牌或人物的侵权。
