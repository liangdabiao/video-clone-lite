---
name: video-clone-lite
description: 极简视频复刻流水线：参考视频（链接/本地文件）→ GLM 直传理解分镜 → 换主角换产品或高保真重绘 → Pippit 逐镜头生成 → ffmpeg 合成出片。当用户提到"复刻视频、做同款、仿这条视频、clone video、换个主角/产品重拍、生成同款短视频、带货同款、把这条片子重做一版"时使用。依赖仅 ffmpeg + apiz CLI + pippit CLI + Python 标准库，禁止安装重型组件。生成会花钱：每次生成前必须先向用户报价，未经确认绝不调用付费接口。
---

# video-clone-lite — 三段式视频复刻（v2，实战验证）

把一条爆款视频变成你的新视频。单一事实来源是项目目录里的 `plan.json`
（分镜表）；每一步产物落盘，过程记入项目 `LOG.md`（用户要求可逐步检查调试）。

## 环境四件套（缺一先补，均有一次性初始化）

| 工具 | 用途 | 初始化 |
| --- | --- | --- |
| ffmpeg | 合成/抽帧/探参数 | 一般已装 |
| `apiz` CLI | 理解(备)/上传/对齐/TTS/图片 | `apiz auth login` 存 key（或 `~/.suitui-api-key`）|
| `pippit-tool-cli` | **视频生成主力**（用户自己的账号积分）| `npx @pippit-dev/cli@latest install` → `pippit-tool-cli login` 浏览器登录 |
| Python 标准库 | 脚本 | 无需 pip |

GLM 视频理解另需 `~/.glm_api_key`（首行存 key）。

## 先分清两种复刻模式（动手前必须和用户确认是哪种）

**模式 A「高保真重绘」**：同一个人同一个产品，把原片重新生成一遍。
→ 每镜抽**原片首帧+尾帧**，`--generate-type 1` 首尾帧模式。
适合：修复老素材、重制；画面像原片是必然的。

**模式 B「同结构换内容」（商业核心）**：保留镜头结构/节奏/动作时序/话术，
**换掉主角和产品**。
→ 先生成"新主角参考图+新产品参考图"，每镜传参考图 `--generate-type 0`
参考生成模式；动作时序来自 GLM 理解结果。
适合：带货同款、换自己的产品投放。

## 工作流

### 第 1 步 · 理解（GLM 直传整段视频，约几分钱）

```bash
python scripts/build.py understand <视频> refs/glm-storyboard.json
python scripts/build.py extract <视频> refs        # 抽帧+音频，留作质检对照
```

- `understand` 一次调用产出：逐镜景别/运镜/**连续动作时序**/台词/声音细节
  ——模型看连续运动，信息密度远超抽帧推断；限 ≤40MB 且 ≤120s（超限先转码）
- 台词的权威来源是 ASR（`apiz align`/WhisperX），GLM 可能漏听轻声自语
- 基于理解写 `plan.json`（模板 `templates/plan.json`），**先给用户过目再花钱**

### 第 2 步 · 换内容素材（仅模式 B，几积分）

```bash
apiz generate "<新主角描述>" --model apiz/gpt-image-2.5-flare --wait --json
apiz generate "<新产品描述>" --model apiz/gpt-image-2.5-flare --wait --json
```

主角图要**清晰正脸+目标场景氛围**；产品图要**白底/桌面特写+包装**。
下载到 `refs/character.jpg`、`refs/product.jpg` 并 Read 质检。

### 第 3 步 · 逐镜生成（唯一花钱环节；Pippit 为主力通道）

```bash
python scripts/build.py pgen plan.json           # 干跑：打印计划与余额
python scripts/build.py pgen plan.json --yes     # 用户确认后提交+自动轮询收片
python scripts/build.py pgen plan.json --yes --only D   # 只重做某一镜
```

- **模式 B**：plan 每镜 `"refs": ["refs/character.jpg", "refs/product.jpg"]`
  （generate_type 0 参考生成）；**模式 A**：refs 传原片首尾帧两图
  （generate_type 1）
- 实测价格：Seedance_2.5 720p = **20积分/秒**（Pippit 账户按秒扣）；
  模型时长下限 4 秒 → 短镜头按 4s 生成，assemble 按 plan 时长裁剪
- 约 5 分钟/镜；提交限频 1 次/分钟（脚本已自动间隔与重试）

### 第 4 步 · 合成（零成本）

```bash
python scripts/build.py assemble plan.json
```

按 plan 时长逐镜裁剪 + 统一规格 + concat（可选烧 srt、混 BGM）→ `out/final.mp4`。
完成后**Read 抽帧自查**，再请用户播放验收运动/声音（agent 听不到音频、看不到连续
运动——这两项的验收必须交给用户，并明确说出来）。

## 语音与字幕（apiz CLI，已实测）

```bash
python scripts/build.py srt <视频/音频> "台词1|台词2" out.srt   # 字级打轴≈10积分
python scripts/build.py tts "文本" out.mp3 [--voice id]        # TTS 配音
python scripts/build.py upload <文件>                          # 免费公网URL
apiz voices list                                               # 音色列表
```

音色克隆/设计走 MCP speak 工具的 `clone_voice`/`design_voice`（详见 references）。

## 费用纪律（不可协商）

1. 任何付费调用前，在对话里报价（模型/秒数/单价/总额）并获用户确认；
   实测价格与预估不符时，停下来讨论
2. 新项目先用 4s 单镜头校准单价，再批量
3. 参考图/上传/理解类免费或几分钱操作可自主进行
4. **遇到卡点（连续失败、通道异常、结果与预期不符）必须停下来和用户讨论，
   不许反复乱试**——每条弯路都记入项目 LOG.md

## 已知坑（实战换来的，不要重蹈）

- 模型目录里有 ≠ 可用：速推 Fal 池会空、上游会 401；换同类通道重试一次即可，
  连续失败换通道
- 本地图片不要转 base64 传命令行（Windows 32K 限制）→ 一律先 `apiz upload`
- Pippit 提交限频 1/分钟（16010 错误）；`pippit-tool-cli` 是 .cmd，
  脚本里必须 `shutil.which()` 解析
- "暂时无法生成"= 平台瞬时失败，重试一次通常就好；连续两次停下来讨论
- GLM 会漏听轻声台词；ASR 才是台词权威
- 更多细节：`references/pippit.md`（Pippit 通道）、`references/suxui-api.md`
  （速推通道）、`references/models.md`（模型与价格）、
  `references/seedance-knowledge.md`（带货提示词方法论）
