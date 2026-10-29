# ai-video-lab · 本地 AI 视频制作实验室

> 仓库定位：`ai-video-lab` —— 一套可复现、零成本起步的**本地 AI 视频制作实验室**（剧本 → 分镜 → 声音 → 合成 → QC），配套开源方法论、技术栈参考与可复用模板。
>
> 核心 = `lab/` 本地练习平台 + 开源方法与技术文档。本项目只保留技术栈、工作流和可复用模板，不包含任何受版权保护的影片、音频、歌词、截图、角色设定或活动物料。

[English summary](#english-summary) · [快速开始](#快速开始) · [仓库结构](#仓库结构) · [许可证](#许可证)

---

## 这是什么

这不是「一句话生成爆款视频」的工具清单，而是一条**有质量门的内容生产流水线**：

```text
主题与受众
   ↓
歌词 / 旁白（先定观点）
   ↓
Suno 出歌（先定时间轴）
   ↓
节拍表（BPM → 小节 → 时间码）
   ↓
分镜与镜头卡（一个镜头一个主动作）
   ↓
资产护照（角色 / 场景 / 道具一致性）
   ↓
开源本地画布（参考图、提示词、多 take、血缘）
   ↓
Seedance 生成（480p 试错，720p 出片）
   ↓
剪映 Skill 粗剪（按 EDL 搭时间轴）
   ↓
人工精剪（表演、节奏、字幕、调色、实拍整合）
   ↓
QC 与发布包
```

核心观点：

1. **声音先行**：先用 Suno 把歌定下来，画面跟着节拍走。
2. **资产护照**：角色、场景、道具的视觉描述被锁死，逐字复用到每个镜头。
3. **画布化生产**：用无限画布管理参考图、提示词、多版本 take 和镜头血缘。
4. **自动粗剪 + 人工精剪**：剪映 Skill 只负责把时间轴搭对，审美与节奏仍然由人决定。
5. **成本可控**：低分辨率试错，只对入选镜头出高分辨率。

---

## 不包含什么

为了便于公开分享和长期维护，本仓库明确**不包含**：

- 任何第三方影片、视频文件、音频、音乐分轨；
- 任何第三方歌词、逐字转录或逐镜头复刻表；
- 任何影片截图、关键帧、角色设定图、活动主视觉；
- 任何公司/活动/账号标识、品牌 Logo、真实聊天记录或个人隐私信息；
- 任何未公开的商业项目素材。

案例讨论采用**匿名化、结构化**的方法：只讨论叙事结构、声音设计、镜头语言、生产流程和成本模型，不复制具体作品的内容。

如果你要在课堂或文章中展示第三方作品，请自行取得权利人授权，或使用你自制/已授权的样片。详见 [DISCLAIMER.md](DISCLAIMER.md)。

---

## 技术栈

| 层 | 工具/项目 | 在流水线中的角色 |
|---|---|---|
| 编排层 | **WorkBuddy** | 制片人：拆任务、写文本、管文件、调工具、做质检 |
| 画布层 | **ComfyUI** / **infinite-canvas** / **Reelvas** 等开源本地画布 | 生产现场：参考图、提示词、多 take、镜头血缘 |
| 视频生成 | **Seedance** | 摄影机：把静帧变成有表演、有运镜、有声音的镜头 |
| 音乐生成 | **Suno** | 作曲：先定歌，再定剪辑节奏 |
| 剪辑 | **剪映专业版** + 剪映草稿 Skill | 剪辑助理：按 EDL 搭时间轴，人来精修 |
| 美术 | 图片生成模型 / 本地模型 | 角色定妆照、场景图、道具图 |
| 交付 | 视频号 / 抖音 / B 站 / 企业大屏 | 横版主片 + 竖版切条 + 静音版 |

> WorkBuddy、Seedance、Suno、剪映、ComfyUI 等名称归其各自权利人所有。本项目与上述公司/项目**无隶属、合作或背书关系**，仅作技术讨论与教学示例。详见 [NOTICE.md](NOTICE.md)。

---

## 仓库结构

| 文件 | 内容 | 用途 |
|---|---|---|
| [01_视频拆解与逆向工程.md](01_视频拆解与逆向工程.md) | 匿名化案例研究方法：叙事、声音、视觉、生产流程四层拆解 | 方法论 |
| [02_工具链技术报告.md](02_工具链技术报告.md) | WorkBuddy、开源画布、Seedance、Suno、剪映 Skill 的定位、能力、接入方式与边界 | 技术栈选型 |
| [03_成本_合规_风险.md](03_成本_合规_风险.md) | 成本测算、合规要求、常见问题与应急预案 | 交付与合规 |
| [04_拉片表模板.md](04_拉片表模板.md) | 逐镜头拉片模板、填写说明与虚构示例 | 分析方法 |
| [05_本地模型与FFmpeg对比.md](05_本地模型与FFmpeg对比.md) | 本地/云端视频模型选型，FFmpeg 与剪映的分工 | 环境搭建 |
| [templates/](templates/) | 可直接使用的 CSV / Markdown 模板 | 实操 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献指南 | 参与维护 |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | 社区行为准则 | 社区治理 |
| [SECURITY.md](SECURITY.md) | 安全问题与敏感内容报告方式 | 安全 |
| [NOTICE.md](NOTICE.md) | 第三方名称与商标说明 | 法律信息 |
| [DISCLAIMER.md](DISCLAIMER.md) | 版权、AI 内容、教学使用免责声明 | 法律信息 |

---

---

## 本地 AI 视频实验室

[`lab/`](lab/) 是一套可复现的**本地练习平台**，把「剧本 → 分镜 → 声音 → 合成 → QC」串成六个阶段，默认走零成本路径，任何一步都可单独重跑：

```powershell
# 一步跑完（初始化 + 导入示例剧本 + 分镜 + 声音 + 合成 + QC）
python lab\run.py all --project lab\projects\demo

# 分步执行
python lab\run.py import-script --input lab\examples\example_script.md --project lab\projects\demo
python lab\run.py storyboard --project lab\projects\demo
python lab\run.py audio --project lab\projects\demo
python lab\run.py composite --project lab\projects\demo
python lab\run.py qc --project lab\projects\demo

# 本地 Web 练习台（纯标准库，可选）
python lab\server.py --port 8765
```

| 阶段 | 命令 | 默认引擎 | 可切换 |
|---|---|---|---|
| 初始化 | `init` | 本地 | — |
| 剧本导入 | `import-script` | 文本解析 | 任意 LLM（百炼/豆包） |
| 分镜制作 | `storyboard` | 规则引擎（动作节拍拆分 + 提示词生成） | 本地 LLM |
| 声音制作 | `audio` | SAPI 占位念白 | Suno 每日积分 |
| 合成 | `composite` | FFmpeg（占位色块兜底） | 实拍素材 / 本地 Wan / Seedance / 剪映 |
| 质检 | `qc` | ffprobe | — |

> 本地 Wan 2.2（1.3B/5B GGUF）是**可插拔视频引擎**：若本地环境就绪则生成草稿镜头，否则自动回退为占位色块，保证链路不断。所有项目产物写入 `lab/projects/`，已被 `.gitignore` 忽略，不进公开仓库。详见 [`lab/README.md`](lab/README.md)。

### 实拍素材 + Ark 凭据配置

#### 实拍素材路径（零云端成本、有真实人物感）

有真实/授权实拍素材时，把它按镜头命名放进项目素材目录，合成时选 `footage` 引擎即可直接拼接：

```powershell
# 目录：lab\projects\<name>\assets\footage\
#   S01.mp4 / S02.mov / S03_001.mp4 …（按镜头 ID 匹配，大小写不限，支持前缀）
python lab\run.py composite --project lab\projects\demo --engine footage
```

- `footage_path()` 按镜头 ID 在 `assets/footage/` 找素材；找到就 FFmpeg 转码（等比缩放 + 黑边补齐、裁剪到镜头时长）。
- 某镜头没有对应素材时自动回退占位色块，链路不断。
- 管理台引擎徽章显示「实拍素材 (N)」。
- 适合：实拍/授权样片打底 + AI 风格层。

#### Ark 凭据（云端 Seedance 引擎）

Seedance 模型**闭源**（字节跳动），只能走火山方舟（Ark）云 API，需配置两个环境变量：

| 变量 | 含义 | 注意 |
|---|---|---|
| `ARK_API_KEY` | 访问密钥（鉴权 + 计费凭据） | 从方舟控制台「API Key 管理」创建；**绝不写进仓库文件** |
| `ARK_MODEL_ID` | Seedance 模型标识 | 模型广场复制；是**模型 ID**，不是 `ep-` 开头的 endpoint ID |

```powershell
setx ARK_API_KEY "你的key"
setx ARK_MODEL_ID "你的模型ID"
# 重启管理台 → 引擎徽章「云端 Seedance」变绿 → 合成阶段选 seedance
```

- 未配置时 `seedance.is_ready()` 返回 False，合成**安全回退**占位/实拍，不报错。
- 新用户通常有**免费/赠送 token 额度**，可先试跑。
- 密钥只放环境变量，`.gitignore` 已忽略 `.env`；管理台仅监听 `127.0.0.1`，不暴露公网。

---

## 快速开始

1. 阅读 [`01_视频拆解与逆向工程.md`](01_视频拆解与逆向工程.md)，理解「叙事—声音—视觉—生产」四层拆解法。
2. 阅读 [`02_工具链技术报告.md`](02_工具链技术报告.md)，按预算与硬件选择画布与视频模型。
3. 复制 [`templates/`](templates/) 到新项目目录，或用 `lab/` 的六阶段流水线（`lab/run.py all`）。
4. 用 [`templates/00_concept.md`](templates/00_concept.md) 写一句话主题。
5. 用 [`templates/08_lyrics_template.md`](templates/08_lyrics_template.md) 写歌词，再用 Suno 出歌。
6. 用 [`templates/02_beat_sheet.csv`](templates/02_beat_sheet.csv) 和 [`templates/03_shot_list.csv`](templates/03_shot_list.csv) 做节拍表与镜头卡。
7. 用 [`templates/04_asset_passport.md`](templates/04_asset_passport.md) 锁角色/场景（跨镜头一致性锚点）。
8. 用 `lab/` 的提示词生成器生成 Seedance 提示词，或按 `02` 工具链报告接入画布生成。
9. 用 [`templates/05_edl.csv`](templates/05_edl.csv) 和剪映 Skill 粗剪，再人工精剪。
10. 用 [`templates/06_qc_checklist.md`](templates/06_qc_checklist.md) 做发布前检查。

> 模板中的示例均为虚构示例，不对应任何真实影片、品牌或人物。

---

## 关键方法

### 1. 拉片：只看结构，不抄内容

拉片要回答四个问题：

1. 它说了什么（叙事/观点）？
2. 它怎么拍（景别/机位/运镜/光线）？
3. 它怎么剪（节奏/转场/音画关系）？
4. 它怎么做得出来（AI/实拍/后期/成本）？

**只学结构、节奏、方法和判断，不复制具体画面、歌词、角色或镜头序列。**

### 2. 资产护照：一致性靠「不改」

把角色、场景、道具写成可执行的视觉描述，每个镜头提示词逐字复用，只改动作、机位和情绪。参考图优先级：

```text
角色定妆照 > 场景图 > 首帧 > 纯文字描述
```

### 3. 一个镜头只干一件事

一个 5 秒镜头只写一个主动作、一个运镜。想讲四件事，就拆四个镜头。

### 4. 先算账，再开跑

```text
视频成本 = 成片秒数 × 每秒单价 × 重抽倍数
总成本 = 视频 + 图片 + 音乐 + Agent/订阅 + 人工 + 杂项
```

新手重抽倍数通常 3–5×，熟练后 1.5–2.5×。低分辨率试错、只对入选镜头出高分辨率，是最有效的省钱方式。

---

## 适合谁

- 自媒体/短视频创作者，想升级「AI 味」重的口播/图文号；
- 企业市场/品牌/活动策划，要做预热片、主题曲、展会视频；
- 设计师/插画师，想把静态作品变成动态 IP；
- 教师/培训师，想做教学宣传片或知识类视频；
- 独立开发者/小团队，想低成本做产品发布片。

---

## 贡献

欢迎提交：

- 新的匿名化教学案例（必须使用自制或已授权素材）；
- 工具链适配说明、排障记录、成本实测；
- 模板改进、英文翻译、无障碍与可读性改进；
- 合规与伦理相关的修订建议。

请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。

**禁止提交**：第三方影片/音频/歌词/截图、真实品牌活动物料、未授权的人脸/声音、API Key、客户隐私数据。

---

## 许可证

本项目采用双许可证：

- **代码与脚本**：MIT License，见 [LICENSE](LICENSE)；
- **文档、课程设计与模板**：Creative Commons Attribution 4.0 International（CC BY 4.0），见 [LICENSE-docs](LICENSE-docs)。

你可以自由使用、修改、再分发，并用于商业教学，但请保留署名与许可证声明。第三方工具、商标和素材仍归其各自权利人所有。

---

## 免责声明

- 本项目不提供法律意见；合规要求以你所在司法辖区的最新法律法规和平台规则为准。
- AI 生成内容可能涉及版权、肖像权、商标权、广告法与平台审核风险，发布前请自行核查。
- 本项目不保证任何工具的价格、功能、可用性或商用条款长期不变。
- 课程中的收益、成本、耗时均为示例估算，不构成收益承诺。

完整声明见 [DISCLAIMER.md](DISCLAIMER.md)。

---

## English summary

**ai-video-lab — a local AI video production lab + open methods & tech reference.**

This repository documents a reproducible, low-cost local lab (script → storyboard → sound → composite → QC) with open methods, tech-stack notes and reusable templates:

```text
theme → lyrics → Suno → beat sheet → shot list → asset passport
      → open-source canvas → Seedance → Jianying draft → human fine-cut → QC
```

The video engine is pluggable: **real footage** (`assets/footage/`, zero-cost, real-person look) or **cloud Seedance** (needs `ARK_API_KEY` + `ARK_MODEL_ID`), with a local Wan draft fallback for previs.

It includes templates, prompt patterns, cost models, and compliance checklists. It does **not** include any third-party video, audio, lyrics, screenshots, character designs, event branding, or private chat records. The case-study method is anonymized and focuses on structure and production logic, not content reproduction.

Licensed under MIT (code) and CC BY 4.0 (documentation and templates). Tool names and trademarks belong to their respective owners; no affiliation or endorsement is implied.
