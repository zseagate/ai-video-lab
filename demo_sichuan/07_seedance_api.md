# 07 Seedance 镜头生成说明

> Seedance 是火山方舟的云端视频生成服务，本地不能安装。  
> 需要：火山引擎账号、方舟开通、API Key、模型 ID、额度。  
> 当前项目只准备提示词和 API 占位脚本，不在没有授权的情况下调用。

## 推荐流程

1. 用 ComfyUI 生成 5 张关键帧（S01–S05），16:9，1280×720 或 720p。
2. 把关键帧作为 Seedance 的「首帧图」。
3. 每个镜头生成 5 秒，5 个镜头 = 25 秒。
4. 第 6 个镜头（标题卡）用 ComfyUI/矢量图生成，或直接用 CapCut 做。
5. 导出 5 段 mp4，放进 `demo_sichuan/assets/seedance/`。
6. 用 CapCut 或 ffmpeg 拼接、加字幕、调色。

## 镜头清单

| 镜头 | 时长 | 首帧 | 运动 |
|---|---|---|---|
| S01 | 5s | 雨夜茶馆外景 | 缓慢推近，雨滴、灯笼微摆、蒸汽上升 |
| S02 | 5s | 盖碗茶特写 | 手揭盖碗，蒸汽旋转，雨窗散景 |
| S03 | 5s | 变脸舞台 | 快速横移，扇子开合，脸谱红/黑/金切换 |
| S04 | 5s | 火锅微距 | 缓慢下摇，红汤翻滚，筷子夹毛肚 |
| S05 | 5s | 雨巷红灯笼 | 跟拍，人物行走，雨丝、湿地反光 |
| S06 | 5s | 标题卡 | 轻微推近，金色标题微光 |

## 通用负面提示词

```text
panda, panda costume, panda rap, photorealistic skin, anime face, extra fingers, distorted hands, face morphing, inconsistent costume, brand logos, watermark, captions, readable text, neon overload, sci-fi, clutter, fast random cuts, camera shake, flicker, duplicate objects, melted objects
```

## API 占位

脚本：`demo_sichuan/tools/seedance_api.py`

先只检查环境变量：

```powershell
python demo_sichuan\tools\seedance_api.py --check-env
```

需要先设置环境变量：

```powershell
$env:ARK_API_KEY = "你的火山方舟 API Key"
$env:ARK_MODEL_ID = "你的 Seedance 模型 ID"
```

只打印请求，不调用 API：

```powershell
python demo_sichuan\tools\seedance_api.py
```

真正调用 Seedance：

```powershell
python demo_sichuan\tools\seedance_api.py --execute
```

如果指定某个镜头：

```powershell
python demo_sichuan\tools\seedance_api.py --prompt-file "demo_sichuan\05_prompts\S03.txt" --image "demo_sichuan\assets\keyframes\S03.png" --out "demo_sichuan\assets\seedance\S03.json" --execute
```

> `--out` 写的是 API 任务响应 JSON，不是最终 mp4。  
> 不同账号的模型 ID、接口版本、计费方式可能不同；以火山方舟控制台为准。  
> 不要把 API Key 写进仓库、截图或聊天记录。
