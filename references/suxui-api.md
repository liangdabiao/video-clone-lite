# 速推AI API 调用参考（CLI 为主，2026-09-21 实测）

## 工具形态

一切能力通过**官方 apiz CLI**（`~/.local/bin/apiz`，v0.3.3+）调用：
`generate` / `models` / `upload` / `transfer` / `align` / `speak` / `voices` /
`parse` / `tasks` / `account` / `auth`。build.py 只依赖 CLI + ffmpeg，
**不需要 MCP 配置**。MCP（suitui-ai HTTP 端点）是同一后端的另一层皮，
仅作为无 CLI 环境的备用方案。

- 密钥：`apiz auth login` 存入 `~/.config/apiz/config.toml`（一次即可），
  或任何命令加 `--api-key sk-...` / 环境变量。不进仓库、不进对话
- 账户：1积分 = 0.01元，`apiz account balance`
- 网关偶发 Cloudflare 520/525：脚本已自动重试；连续失败先报告再处理

## build.py 已封装的命令

| 命令 | 对应 CLI | 花钱 |
| --- | --- | --- |
| `gen` | `apiz generate <prompt> --model X [--image-url U] [--duration n] [--aspect-ratio 9:16] --params '{"resolution":"480p"}' --wait --json` | **是** |
| `srt` | `apiz upload` → `apiz align "<台词>" --audio <URL>`（字级毫秒时间戳） | ≈10积分/次 |
| `tts` | `apiz speak "<文本>" --output-file f.mp3 [--voice id]` | 少量 |
| `upload` | `apiz upload <文件>` → `public_url` | 否 |
| `balance` | `apiz account balance` | 否 |

## 实测备注

- `generate --wait --json` 返回里产物在 `data.output.media[].url`；
  build.py 的 `_media_url()` 已做递归提取 + 正则兜底
- **参数错误（HTTP 400）会在消息里写明该模型要什么**，照改即可，不要猜
- 目录里有模型但提交报"没有可用的 XX 账号"= 该模型当前不可用，换同类
- `--image-size` 这类参数不是所有图像模型都收；不传往往就能跑
- 图像 `image_url` 支持 base64 data URL（本地图内联，build.py 自动转）
- 模型教程：`apiz models docs <id>`；完整参数：`apiz models info <id>`
- 音色克隆/设计（MCP speak 的 `clone_voice`/`design_voice` 动作）：克隆要
  10 秒–5 分钟干净样本；设计音色有时效，用前看返回说明
- STT（台词未知时）：`volcengine/speech-to-text/bigmodel-v2`，2积分/分钟，
  要求公网音频 URL（先 upload）
- **coze-upload 那条借道 coze.cn 的上传路已废**（托管账号额度 4028），勿用

## 花钱纪律

SKILL.md 规定：每次 `gen --yes` 前必须在对话里向用户报价（模型/秒数/单价/
总额）并获确认；新项目先 480p。`estimate`、`balance`、`upload`、`models`、
`parse` 永远免费。
