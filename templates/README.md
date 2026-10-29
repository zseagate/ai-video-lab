# templates 使用说明

> 这些文件可以直接复制到新项目里用。CSV 已做 UTF-8 BOM，Excel/WPS 打开中文不乱码。

| 文件 | 用途 | 用在哪一周 |
|---|---|---|
| `00_concept.md` | 一页纸项目概念卡 | 第 1 周开题 |
| `01_shot_list.csv` | 拉片表（拆别人的片子） | 第 0 周 / 工作坊 Day 1 |
| `02_beat_sheet.csv` | 节拍表（BPM → 小节 → 时间码） | 第 1–2 周 |
| `03_shot_list.csv` | 镜头卡（写自己的片子） | 第 2–4 周 |
| `04_asset_passport.md` | 角色/场景/道具护照 | 第 2 周 |
| `05_edl.csv` | 剪辑决策表（给剪映 Skill 用） | 第 5 周 |
| `06_qc_checklist.md` | 发布前 QC 清单 | 第 5–6 周 |
| `07_cost_log.csv` | 成本记录 | 全程 |
| `08_lyrics_template.md` | 歌词模板 + 押韵速查 | 第 1 周 |
| `09_feedback.md` | 学员反馈表 | 结课 |

---

## 快速开始

1. 新建项目文件夹，按 `05_教学资产包` 的目录结构建好；
2. 复制 `00_concept.md` → 填一句话主题；
3. 复制 `08_lyrics_template.md` → 写歌词；
4. 复制 `02_beat_sheet.csv` → 按 BPM 填小节；
5. 复制 `03_shot_list.csv` → 填镜头卡；
6. 复制 `04_asset_passport.md` → 填角色/场景；
7. 生成后用 `07_cost_log.csv` 记账；
8. 剪辑前把 `03_shot_list.csv` 转成 `05_edl.csv`；
9. 发布前用 `06_qc_checklist.md` 逐项打勾。

---

## CSV 使用提示

- 用 Excel/WPS 打开后，**另存为 UTF-8 CSV**，避免中文乱码；
- 不要合并单元格；
- 不要在一个字段里放英文逗号（会多一列）；需要时用中文逗号或分号；
- 镜头号从 `S01` 开始，两位数，方便排序；
- 时间码统一格式：`00:00:05:00`（时:分:秒:帧）或 `00:05.0`（分:秒），全项目只用一种。
