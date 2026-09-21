# 模型菜单与计价（2026-09-21 实测后更新；用时以实时查询为准）

## 视频生成主力：Pippit 小云雀（用户自有账号积分）

- `Seedance_2.5`（Pippit 默认模型）720p = **20积分/秒**（两次实测一致），
  4–30s，480p/720p/1080p，参考生成/首尾帧/视频编辑/延长四种模式，
  原生同步音频，约 5 分钟/镜
- 其他：seedance2.0_fast_vision、Seedance_2.0_mini(体验版)、MiniMax-H3、
  wan3.0、happyhorse-1.1（价格未实测，用前查）
- 注意：账号是用户自己的（浏览器登录），余额独立于速推积分

## 视频生成备选：速推通道（不推荐主力，容量不稳）

| 模型 ID | 480p | 720p | 1080p |
| --- | --- | --- | --- |
| bytedance/seedance-2.0/fast/* | 43积分/秒 | 97 | — |
| st-ai/super-seed2-lite | — | 50（实测，渲染极慢曾卡70%超40分钟）| — |
| bytedance/seedance-2.0/standard/* | 54 | 121 | 273 |

时长下限 4 秒（auto/4–15）；Fal 账号池可能整池为空（HTTP 500 持续）。
**速推通道仅在 Pippit 不可用时作为备份。**
- 预扣后按 token 多退少补的 `ark/seedance-2.0` 也可，计价方式不同，见 guide

## 图像（角色定妆图/首帧图）

`fal-ai/nano-banana-2`、`fal-ai/flux-2/flash`（快）、`apiz/gpt-image-2.5-*`、
`fal-ai/bytedance/seedream/v4.5/text-to-image`（中文文字好）、
`xai/grok-imagine-image-2.0/text-to-image`、`qwen-image-edit`（改图）。
单价用 `search_models {"model_id": ...}` 查，生成前报价。

## 语音（已实测，2026-09-21）

- **对齐打轴**：`apiz align "<台词>" --audio <URL>` — 字级毫秒时间戳，
  实测 10 积分/次；**需公网音频 URL**（先 `apiz upload`，免费）
- **TTS**：`apiz speak "<文本>" --output-file x.mp3 [--voice id]`（Minimax
  speech-2.8-hd 等档位）；音色列表 `apiz voices list`（预置音色带试听 URL）
- STT（台词未知时）：`volcengine/speech-to-text/bigmodel-v2`，2积分/分钟，
  MCP generate 调用，同样要公网 URL
- 音色克隆/设计：MCP speak 工具 `clone_voice`（10 秒–5 分钟样本）/`design_voice`
  （自然语言描述）；临时音色有时效（voice-design 168h），克隆音色时效见返回
- BGM：`minimax/music-gen`（风格描述+歌词→原创音乐），价格用 search_models 查

## 上传（免费）

`apiz upload <本地文件>` → 返回 `public_url`（apiz TOS/CDN）。
注意：coze-upload skill 是另一条借道 coze.cn 的路径，其托管账号积分已耗尽
（4028 错误），不要用。

## 免费

`parse_video`（链接解析）、`search_models`、`guide`、`account.balance`。

## 视频理解

**无外部模型**：执行 agent（智谱 GLM）直接用 Read 读抽帧网格自己分析，
零成本。带货向提示词方法论见本 skill `references/seedance-knowledge.md`
（S-A-C-S-C 框架，已内置，独立可用）。

> 本 skill 完全独立：不调用、不依赖任何其他 skill；有用的资料一律复制进本目录。
