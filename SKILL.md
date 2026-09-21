---
name: video-clone-lite
description: 极简视频复刻流水线：参考视频（链接/本地文件）→ GLM 直传理解分镜 → 换主角换产品（保留原片结构/节奏/话术）→ Pippit 逐镜头生成 → ffmpeg 合成出片。当用户提到"复刻视频、做同款、仿这条视频、换个主角/产品重拍、生成同款短视频、带货同款、把这条片子重做一版"时使用。依赖仅 ffmpeg + apiz CLI + pippit CLI + Python 标准库，禁止安装重型组件。生成会花钱：每次生成前必须先向用户报价，未经确认绝不调用付费接口。
---

# video-clone-lite — 三段式视频复刻（同结构换内容）

把一条爆款视频变成你的新视频：**保留原片的镜头结构、节奏、动作时序和话术，
换掉主角和产品。** 单一事实来源是项目目录里的 `plan.json`（分镜表）；
每一步产物落盘，过程记入项目 `LOG.md`（用户要求可逐步检查调试）。

**不做**"照原片逐帧重绘"——用户明确表示永远没有这个需求。所有生成一律
基于"新主角参考图 + 新产品参考图 + 动作时序描述"。

## 环境四件套（缺一先补，均有一次性初始化）

| 工具 | 用途 | 初始化 |
| --- | --- | --- |
| ffmpeg | 合成/抽帧/探参数 | 一般已装 |
| `apiz` CLI | 上传/对齐/TTS/图片生成 | `apiz auth login` 存 key（或 `~/.suitui-api-key`）|
| `pippit-tool-cli` | **视频生成主力**（用户自己的账号积分）| `npx @pippit-dev/cli@latest install` → `pippit-tool-cli login` 浏览器登录 |
| Python 标准库 | 脚本 | 无需 pip |

GLM 视频理解另需 `~/.glm_api_key`（首行存 key）。

## 工作流

### 第 1 步 · 理解（GLM 直传整段视频，约几分钱）

```bash
python scripts/build.py understand <视频> refs/glm-storyboard.json
python scripts/build.py extract <视频> refs        # 抽帧+音频，留作成片对照
```

- `understand` 一次调用产出：逐镜景别/运镜/**连续动作时序**/台词/声音细节
  ——模型看连续运动，信息密度远超抽帧推断；限 ≤40MB 且 ≤120s（超限先转码）
- 台词的权威来源是 ASR（`apiz align`/WhisperX），GLM 可能漏听轻声自语
- 基于理解写 `plan.json`（模板 `templates/plan.json`）：结构照搬原片切点，
  动作描述照搬 GLM 的 action_steps，**主体/产品换成用户的新内容**
  （如"精华泵瓶"→"口红"、"外国博主"→"中国 20 岁女性"），**先给用户过目**

### 第 2 步 · 新内容参考图（几积分，apiz gpt-image-2.5）

```bash
apiz generate "<新主角描述：清晰正脸+目标场景氛围>" --model apiz/gpt-image-2.5-flare --wait --json
apiz generate "<新产品描述：产品特写+包装+同场景光感>" --model apiz/gpt-image-2.5-flare --wait --json
```

下载到 `refs/character.jpg`、`refs/product.jpg` 并 **Read 质检**：
脸要清晰、产品要与原片气质同调（同光感同场景）。用户自备照片可直接用。

### 第 3 步 · 逐镜生成（唯一花钱环节；Pippit 参考生成模式）

```bash
python scripts/build.py pgen plan.json           # 干跑：打印计划与余额
python scripts/build.py pgen plan.json --yes     # 用户确认后提交+自动轮询收片
python scripts/build.py pgen plan.json --yes --only D   # 只重做某一镜
```

- 每镜 `refs` 必传**新主角参考图**（跨镜身份一致的锚），涉产品的镜追加产品图
- 实测价格：Seedance_2.5 720p = **20积分/秒**；模型时长下限 4 秒 →
  短镜头按 4s 生成，assemble 按 plan 时长裁剪
- 约 5 分钟/镜；提交限频 1 次/分钟（脚本已自动间隔与重试）

### 第 4 步 · 合成（零成本）

```bash
python scripts/build.py assemble plan.json
```

按 plan 时长逐镜裁剪 + 统一规格 + concat（可选烧 srt、混 BGM）→ `out/final.mp4`。
完成后 **Read 抽帧自查**（结构/主角一致性/产品一致性），再请用户播放验收
运动/声音/台词——**agent 听不到音频、看不到连续运动，这两项的验收必须
交给用户并明确说出来**。

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
- 本地图片不要转 base64 传命令行（Windows 32K 限制）→ 生成用图先 `apiz upload`
  （Pippit 的 `--image` 传本地路径即可，CLI 内部自动上传）
- Pippit 提交限频 1/分钟（16010 错误）；`pippit-tool-cli` 是 .cmd，
  脚本里必须 `shutil.which()` 解析
- "暂时无法生成"= 平台瞬时失败，重试一次通常就好；连续两次停下来讨论
- GLM 会漏听轻声台词；ASR 才是台词权威
- 更多细节：`references/pippit.md`（Pippit 通道）、`references/suxui-api.md`
  （速推通道）、`references/models.md`（模型与价格）、
  `references/seedance-knowledge.md`（带货提示词方法论）
