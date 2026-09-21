# Pippit 小云雀通道（视频生成主力，2026-09-21 实战验证）

## 是什么

字节系 Pippit（小云雀）的官方 CLI：`pippit-tool-cli`。
视频生成走**用户自己的 Pippit 账号和积分**，不走速推余额。

- 安装：`npx @pippit-dev/cli@latest install`（同时装 xyq-skill 等技能包）
- 登录：`pippit-tool-cli login`（浏览器流程，一年有效）；`status` 查状态
- 余额：`pippit-tool-cli get-credit-balance`（JSON `total_remain_amount`）
- 模型：`pippit-tool-cli model list` / `model describe <Key>`（含创建模式/
  时长/分辨率配置，缓存 5 分钟，`--refresh` 刷新）

## 生成命令（build.py pgen 已封装，以下为手动用法）

```bash
pippit-tool-cli generate-video \
  --prompt "<分镜动作描述>" \
  --model Seedance_2.5 \
  --generate-type 0 \        # 0=参考生成(换内容)；1=首尾帧(高保真)
  --image refs/character.jpg \   # 参考图可重复传多张；本地路径自动上传
  --image refs/product.jpg \
  --duration 4 \             # 整数秒，模型下限 4，上限 30（2.5）
  --resolution 720p \        # 480p/720p/1080p
  --ratio 9:16
```

返回 `thread_id` + `run_id`（+网页链接）。收片：

```bash
pippit-tool-cli query-result --thread-id T --run-id R --download-dir out
```

`completed: true` 时 `videos[0].output_path` 是已下载到本地的文件，改名归位即可。

## 计费（实测）

- Seedance_2.5 720p：**20积分/秒**（80积分/4s 镜实测两次无误）
- 预扣制：提交即锁定预计积分，失败会退回（实测"暂时无法生成"未扣费）
- 参考图/首尾帧/原生音频不另计费

## 限制与坑（全部踩过）

| 坑 | 处置 |
| --- | --- |
| 提交限频 1 次/分钟（ret=16010 操作过于频繁）| 提交间隔 ≥65 秒；脚本已内置 |
| "暂时无法生成"（创作失败）| 平台瞬时失败，等 65 秒重试一次；连续两次停下讨论 |
| `pippit-tool-cli` 是 `.cmd` | Python subprocess 必须 `shutil.which()` 解析，否则 WinError 2 |
| 首尾帧模式仍缺 `ratio` | 必须显式 `--ratio`，即使模式描述写"adaptive" |
| `--wait` 10 分钟超时但任务仍在跑 | 改用 `apiz tasks ...` 不适用；Pippit 用 query-result 轮询 |

## 实测性能

- 渲染约 **3–5 分钟/镜**（4–5s 720p），支持多任务并行提交后统一轮询
- 参考生成模式的**主角跨镜一致性很好**（同一张参考图贯穿五镜，脸型/发型/
  服装保持）；产品一致性同样可靠
- 原生音频：含环境音；prompt 里写"对镜头说 XXX"可触发台词（内容需人工验收）

## 与速推通道的分工

| 能力 | 通道 |
| --- | --- |
| 视频生成（参考/首尾帧）| **Pippit**（快、便宜、稳）|
| 词级对齐/字幕 | 速推 `apiz align` |
| TTS/音色 | 速推 `apiz speak` / MCP speak |
| 图片生成（参考图）| 速推 `apiz generate`（gpt-image-2.5-flare，~5积分/张）|
| 公网URL | 速推 `apiz upload`（免费）|
| 链接解析 | 速推 `apiz parse`（免费）|
