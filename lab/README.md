# 本地 AI 视频制作实验室（Local AI Video Lab）

> 目标：在本地用最低成本把「剧本 → 分镜 → 声音 → 合成 → QC」跑通，作为可离线、低配可用的**制作与练习平台**。
> 原则：本地优先、零成本起步；优先零推理路径（关键帧动效、实拍素材、FFmpeg 合成），可选本地小 LLM 与云端 Seedance；任何一步都可单独重跑。

## 快速开始

```powershell
# 0. 环境自检（离线，报告 ffmpeg / 模型 / 引擎就绪）
python lab\run.py doctor

# 1. 初始化一个项目
python lab\run.py init --project lab\projects\demo

# 2. 导入剧本
python lab\run.py import-script --input lab\examples\example_script.md --project lab\projects\demo

# 3. 生成分镜 / 镜头卡 / 提示词
python lab\run.py storyboard --project lab\projects\demo

# 4. 生成占位声音（本地 SAPI 念白；正式版换 Suno）
python lab\run.py audio --project lab\projects\demo

# 5. 合成（默认按低配设置；可选叠化转场 / 字幕）
python lab\run.py composite --project lab\projects\demo --transition fade --xfade 0.5 --subtitles

# 6. 质检
python lab\run.py qc --project lab\projects\demo

# 一步跑完（除导入外全部执行）
python lab\run.py all --project lab\projects\demo
```

### 低配模式与本地模型

```powershell
# 开启低配模式：854x480 / 16fps，合成默认用 kenburns（纯 FFmpeg，无推理）
python lab\run.py low-spec --on
python lab\run.py low-spec --off

# 本地小 LLM：查看 / 下载模型（ModelScope，约 470MB 起）
python lab\run.py models --list
python lab\run.py models --download qwen2.5-0.5b-instruct-q4
```

- 模型存放在 `models/`（已 gitignore），下载一次后**离线可用**。
- 未安装模型时，提示词增强自动回退规则引擎；未安装 `llama-cpp-python` 时完全不影响主流程。


## 本地 Web 管理台（图形化，可选）

```powershell
python lab\server.py --port 8765
# 浏览器打开 http://127.0.0.1:8765
```

管理台提供：项目列表/新建、六阶段一键运行、引擎就绪状态（FFmpeg / 关键帧动效 / 实拍 / 本地 Wan / 云端 Seedance / 本地 LLM）、成片预览、故事板/镜头清单/manifest/config 查看、运行日志、**低配模式开关、关键帧管理器、本地模型下载**。纯标准库实现，无需额外依赖。

## 六个阶段

| 阶段 | 命令 | 做什么 | 默认引擎 |
|---|---|---|---|
| 1 初始化 | `init` | 创建项目目录结构 | 本地 |
| 2 剧本导入 | `import-script` | 解析标题/一句话/场景，生成 manifest | 文本解析 |
| 3 分镜制作 | `storyboard` | 剧本拆分成镜头（动作节拍）+ 自动生成 Seedance 提示词 | 规则引擎 `promptgen`（可换 LLM） |
| 4 声音制作 | `audio` | SAPI 占位念白；正式换 Suno 音频 | SAPI / Suno |
| 5 合成 | `composite` | FFmpeg 拼接镜头 + 混音 + 导出 | FFmpeg（kenburns / footage / seedance / wan） |
| 6 质检 | `qc` | 时长、流、体积、音画同步检查 | ffprobe/ffmpeg |

## 可插拔引擎

| 环节 | 零成本默认 | 可切换 |
|---|---|---|
| 文本 | 内置解析 + 模板 | 本地小 LLM（GGUF）/ 任意 LLM |
| 视频 | 关键帧动效 `kenburns`（纯 FFmpeg） | 实拍素材 / 本地 Wan / Seedance / 可灵 / 万相云 API |
| 声音 | SAPI 念白占位 | Suno 每日积分 |
| 合成 | FFmpeg | 剪映/CapCut 精修 |

> 合成引擎选择顺序（`composite.py`）：`reuse`（已有片段）→ `footage`（实拍）→ `seedance`（云端）→ `wan_local`（本地草稿）→ `placeholder`；显式 `--engine kenburns` 时走关键帧动效。低配模式把默认引擎设为 `kenburns`。

> 本地 Wan 视频引擎为「可插拔」：若 ComfyUI + Wan 2.1 T2V 1.3B 模型就绪且服务在跑（`lab/wan.py` 检测），合成阶段会经 ComfyUI 渲染 480p 草稿；否则自动回退为占位色块，保证链路不断。注意 CPU 上渲染很慢（9 帧 / 10 步也需数分钟到十几分钟），草稿请用小帧数、低步数；正式镜头交给云端引擎或 GPU 机器。
> 所有生成物默认写入 `lab/projects/<name>/`，该目录已被 `.gitignore` 忽略，不进公开仓库。

## 分镜 + Seedance 提示词工作流（重点能力）

云端成片的前提是「剧本 → 分镜 → 提示词 → 工作流把控」。本实验室已把这一链做成规则引擎驱动、离线可用的重点能力：

### 剧本拆分分镜（`storyboard.py`）
- 每场剧本按**动作节拍**拆成 1..N 个镜头：`detect_beats()` 识别「动作开启 / 细节特写 / 节奏蒙太奇 / 转场运动 / 收束定格 / 叙事」等动词线索（开扇、合扇、蒙太奇、跨出、特写…）。
- 每个节拍映射到景别 + 运镜 + 时长：如 `动作开启`→中景/推近/4s，`细节特写`→特写/推近/3s，`节奏蒙太奇`→近景/横移/2.5s，`转场运动`→全景/跟随/4s，`收束定格`→中近景/拉远/4s。
- 输出 `shot_list.csv`（含 `shot_size/camera/action/function/prompt_file`）+ `storyboard.md`。
- 示例：4 场剧本 → **6 个镜头**（第一场开扇拆成 中景+特写，第三场蒙太奇拆成 近景+特写）。

### 自动生成 Seedance 提示词（`promptgen.py`）
- 规则驱动的**十层结构化提示词**，风格兼容 Seedance 2.0（参考 `Emily2040/seedance-2.0`、`dexhunter/seedance2-skill`）：
  `subject / action / character / environment / lighting / camera / style / consistent / format / negative`
- **环境层从剧本正文动态提取**（非写死）：任意剧本的设定关键词（如「星际快递员」→霓虹/桥/雨夜，「茶馆」→茶馆/舞台/川西）都会自动识别组合成英文描述，**不固定于某一类题材**。
- 景别/运镜/光线词汇映射到 Seedance 能识别的英文术语（`medium shot, slow push-in` 等）。
- 负面约束固定（`no text, no watermark, no extra fingers, no warped face, no style drift…`），避免常见伪影。
- 镜头时长写入 `format`（如 `16:9, 4.0 seconds`）。

### 跨场景一致性锚点（关键：解决「分场景生成内容不连贯、有差异」）
- 每个项目维护一份 `story_style.json`（角色 / 服装 / 关键道具 / 场景基调 / 色彩风格）。
- `extract_style()` 从剧本**自动提取**主角（按「小X/阿X/老X + 高频出现」启发式，如 `小禾`、`小雷`）、道具、设定、色调；管理台可**编辑微调**。
- 生成的**每一个镜头提示词都注入相同的 `character:` 与 `consistent:` 层**：
  - `character: 小禾, wearing 戏服`
  - `consistent: same character throughout, same costume (戏服), same props (折扇、盖碗…), same setting (茶馆、舞台、雨夜…), same palette (warm red, gold…) — no style drift between shots`
- 因此即使每个场景/镜头**分别提交** Seedance，人物、服装、道具、色彩基调也保持一致 → 前后连贯。
- 保存锚点时 `/api/style/save` 会**自动重同步全部镜头提示词**（批量统一）。

### 提示词优化（`promptgen.optimize()`）
- 缺失层自动补齐、重复层去重、自由文本折叠进 `action`、统一层顺序。
- 若 `character:/consistent:` 与锚点不一致（被手改漂移），优化时会**自动同步回锚点**，保证全片一致。
- 可离线跑，无 LLM 依赖；需要语义级改写时，用 `promptgen.optimize(..., use_llm=True)` 或管理台「🧠 LLM 增强」，无模型时自动回退规则引擎。

### 批量推进（导入 → 分镜 → 提示词一步到位）
- `/api/pipeline/import`：给定项目名 + 剧本文本，**一键** 新建项目 + 导入剧本 + 拆分分镜 + 生成 Seedance 提示词 + 提取一致性锚点。
- 管理台「🚀 批量导入并生成分镜」：选文件或粘贴 → 批量生成整个前期流程。

### 工作流把控（管理台「提示词工作台」+「一致性锚点」）
- **一致性锚点面板**：5 个字段（角色/服装/道具/场景/色调），「重新提取」从剧本生成候选、「保存并同步」写回并重同步所有镜头提示词。
- **提示词工作台**：逐镜头列出 `shot / 景别 / 运镜 / 功能 / 时长 / 提示词首行`；每镜头可 **编辑 / 优化 / 重生成**；顶部可 **重建分镜+提示词**、**全部重新生成**。
- API：`/api/shots`、`/api/style`、`/api/style/save`、`/api/prompt/{regenerate,optimize,save}`、`/api/storyboard/rebuild`、`/api/pipeline/import`。
- 提示词写入 `prompts/Sxx.txt`，合成阶段（本地 Wan / 云端 Seedance）直接读取使用。

## 实拍素材引擎（可插拔）

**有真实/授权实拍素材时**，把它放进 `lab/projects/<name>/assets/footage/`，按镜头命名（`S01.mp4`、`S02.mov`…，大小写不限，也支持 `S01_xxx.mp4` 前缀匹配），然后：

```powershell
python lab\run.py composite --project lab\projects\demo --engine footage
# 或管理台：合成阶段引擎选 footage
```

- `footage_path()` 按镜头 ID 在 `assets/footage/` 找素材；找到就用 FFmpeg 转码（等比缩放+黑边补齐到项目规格、裁剪到镜头时长）。
- 某镜头**没有对应素材**时自动回退占位色块，链路不断。
- 管理台引擎徽章会显示「实拍素材 (N)」。
- 适用：实拍/授权样片打底 + AI 风格层，零云端成本、有真人实拍感。

## 关键帧动效引擎 `kenburns`（低配出片核心）

**不需要任何视频模型**：把一张静帧用 FFmpeg `zoompan` 变成有运镜的镜头。4 核 CPU 渲染 5 秒镜头只需几秒。

- 素材：`lab/projects/<name>/assets/keyframes/S01.png`（也支持 jpg/jpeg/webp/bmp；无图时自动生成渐变色卡）。
- 运镜取自 `shot_list.csv` 的 `camera` 字段（缓慢推近/推近/拉远/横移/环绕/固定/手持/跟随/上升）。
- 为避免 FFmpeg `zoompan` 的累积缩放抖动（trac #4298），所有缩放/平移都按输出帧号**绝对计算**。

```powershell
python lab\run.py composite --project lab\projects\demo --engine kenburns
# 管理台：合成阶段 →「关键帧动效」
```

- 关键帧可以是手绘、实拍截图、或任意图片模型生成的图 → 立刻得到可看的动态分镜。
- 管理台「关键帧管理器」支持上传/删除，按镜头号命名。

## 本地小 LLM 提示词增强（可选，离线）

- `stages/llm_enhance.py`：用 `llama-cpp-python` + 小 GGUF（如 Qwen2.5-0.5B/1.5B-Instruct Q4）改写提示词，再经规则引擎归一化，**强制保留**十层结构与跨镜头一致性锚点。
- 无模型 / 无依赖时自动回退 `promptgen.optimize()`，返回 `engine: rules`，主流程不受影响。
- 低配参数：`n_ctx=2048`、`n_threads` 取 CPU 核数一半（最多 4），懒加载、可 `reset()` 释放内存。
- 模型管理：`lab/stages/models.py`，从 ModelScope 下载到 `models/`，校验 GGUF magic；`run.py models` / 管理台「本地引擎」面板。

## 低配模式与本地优先

- `python lab\run.py low-spec --on`：854×480 / 16fps，合成默认 `kenburns`，避免任何大模型推理。
- 设置持久化在 `lab/low_spec.json`（gitignore），管理台顶部一键切换。
- `python lab\run.py doctor`：离线自检 Python / FFmpeg（`FFMPEG_BIN` → `bin/` → PATH → CapCut → imageio）/ llama-cpp / 模型 / 各引擎就绪状态，不发任何网络请求。
- FFmpeg 统一解析在 `stages/env.py`，不再写死机器路径；可用 `FFMPEG_BIN` 覆盖。

> 工程理念参考了本地优先视频编辑器 [Concat](https://github.com/jub0t/Concat)（Rust + FFmpeg 7，AGPL-3.0）的「离线优先、模型按需下载、关键帧动效、代理预览」思路；本项目**未复制其任何代码**，全部为独立的 Python + FFmpeg 实现。

## 转场与字幕（可选）

```powershell
# 叠化转场（0.5s），支持 fade/wipeleft/wiperight/slideleft/slideup/circleopen
python lab\run.py composite --project lab\projects\demo --transition fade --xfade 0.5

# 烧录字幕：读取 shot_list.csv 的 subtitle（或 caption）列
python lab\run.py composite --project lab\projects\demo --subtitles
```

- 转场用 FFmpeg `xfade`，自动统一各片段为 CFR，再按累计时长计算 offset；时长会比硬切少 `(N-1) × xfade`。
- 字幕用 `drawtext` + 文本文件，自动查找中文字体（`msyh.ttc` / `simhei.ttf` / PingFang / Noto CJK）；无字体时跳过并在结果里返回 `subtitle_note`。
- 管理台合成阶段新增「叠化转场」「字幕」按钮；API 支持 `transition/xfade/subtitles` 参数。
- 声音仍是顺序拼接，转场默认按 `-shortest` 收尾（练习足够；正式交付可在剪映精修对齐）。

## 练习工作台与成本测算

管理台「练习工作台」提供三个零推理练习：

1. **剧本 → 分镜 + 提示词**：粘贴剧本 + 项目名，一键生成练习项目（等同 `/api/pipeline/import`）。
2. **成本测算**：输入秒数 / 引擎 / 重抽次数，调用 `/api/cost` 给出 CNY 区间。也可以命令行：
   ```powershell
   python lab\run.py cost --seconds 60 --engine seedance --retakes 2
   ```
3. **提示词对比**：同一镜头分别走规则引擎与本地 LLM，用 `/api/prompt/preview` **不写盘**展示两者差异，适合课堂演示「十层结构 / 一致性锚点」到底补了什么。

成本口径（`stages/cost.py`，保守估算，非实时报价）：

| 引擎 | 每个 5s 镜头 | 说明 |
|---|---|---|
| kenburns / footage / placeholder | ¥0 | 纯 FFmpeg / 已有素材 |
| wan_local | ¥0.05–0.2 | 仅电费与时间 |
| seedance | ¥8–22 | 按方舟实际计费为准 |



已就绪的本地组件（`lab/wan.py` 自动探测）：

| 组件 | 位置 | 状态 |
|---|---|---|
| ComfyUI | `ComfyUI/` | 已安装，`main.py` 可跑 |
| ComfyUI-GGUF | `custom_nodes/ComfyUI-GGUF` | 已装（GGUF 加载） |
| ComfyUI-WanVideoWrapper | `custom_nodes/ComfyUI-WanVideoWrapper` | 已装（Wan 工作流） |
| Wan 2.1 T2V 1.3B fp16 | `models/diffusion_models/` | 已下载（2.8 GB） |
| UMT5 XXL fp8 文本编码器 | `models/text_encoders/` | 已下载（6.7 GB） |
| Wan 2.1 VAE | `models/vae/` | 已下载（0.25 GB） |

启动 ComfyUI（CPU，无 GPU 机器）：

```powershell
python ComfyUI\main.py --cpu --listen 127.0.0.1 --port 8188
```

渲染一段 480p 草稿（示例，CPU 上较慢）：

```powershell
python lab\wan.py --prompt "a red lantern swaying in the rain at night, cinematic" --out lab\projects\wan_draft.webm
```

> 已实测：`wan_smoke_00001_.webm`（832×480，16fps）在 CPU 上成功产出并转成 mp4。Wan 2.2 5B（720p、官方需 24GB 显存）本机 4GB 显存跑不动，故选用 Wan 2.1 T2V 1.3B 作 480p 草稿引擎。

## 云端引擎（引用开源 Seedance 项目）

**重要事实**：Seedance **模型本体闭源**（字节跳动），没有开源 Seedance 模型；但**云端接入/生产工作流有成熟的开源项目**，可作为本实验室的「云端成片引擎」参考层（本地 Wan 只做预演，真人镜头走云端）。

| 开源项目 | 星 | 许可 | 与实验室的关系 |
|---|---|---|---|
| [Emily2040/seedance-2.0](https://github.com/Emily2040/seedance-2.0) | ~7.9k | MIT | **最贴合**：Seedance 2.0 四模态生产流水线（对应合成/成片阶段） |
| [dexhunter/seedance2-skill](https://github.com/dexhunter/seedance2-skill) | ~4.4k | MIT | 生成 Seedance 2.0 提示词（对应分镜/提示词阶段） |
| [ZeroLu/awesome-seedance](https://github.com/ZeroLu/awesome-seedance) | ~2.8k | MIT | Seedance 2.0 提示词 + API 指南 + 工作流 |
| [liangdabiao/Seedance2-Storyboard-Generator](https://github.com/liangdabiao/Seedance2-Storyboard-Generator) | ~2.7k | — | 剧本→分镜 Skill（对应分镜阶段） |
| [LearnPrompt/awesome-seedance](https://github.com/LearnPrompt/awesome-seedance) | ~2.3k | MIT | Seedance 2.5/2.0 提示词库 + 79 个 AI-video Skills |
| [YouMind-OpenLab/awesome-seedance-2-prompts](https://github.com/YouMind-OpenLab/awesome-seedance-2-prompts) | ~2.2k | — | 2000+ 提示词 + API 指南 |

> 本实验室自带的 `demo_sichuan/tools/seedance_api.py` 是直连火山方舟 API 的轻量客户端；上述开源项目是更完整的流程/Skill 参考。第三方项目名称与商标归其各自权利人所有，本项目仅作技术引用，无隶属或背书关系。

## 目录

```text
lab/
  README.md            本文件
  config.yaml          平台默认配置（含成本模式）
  low_spec.json        低配模式设置（本地生成，gitignore）
  run.py               CLI 编排器（doctor / models / low-spec）
  server.py            本地 Web 练习台（纯标准库）
  static/index.html    Web 界面
  examples/            示例剧本
  stages/              六个阶段 + 引擎
    env.py             ffmpeg 解析 / 低配设置 / doctor
    kenburns.py        关键帧动效引擎（FFmpeg zoompan）
    llm_enhance.py     本地小 LLM 提示词增强（可选）
    models.py          GGUF 模型注册与下载
    cost.py            成本测算（练习工具）
    promptgen.py       十层提示词 + 一致性锚点
    storyboard.py      剧本→分镜
    composite.py       合成（reuse/footage/kenburns/seedance/wan/placeholder）
  projects/            本地项目（git 忽略）
models/                本地 GGUF 模型（git 忽略）
scripts/setup.ps1      Windows 一键安装
scripts/setup.sh       macOS/Linux 一键安装
```
