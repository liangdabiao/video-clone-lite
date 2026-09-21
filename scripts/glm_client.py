"""Shared GLM-5.3-Flash client for the glm vision skill family.

封装了实测验证过的所有 API 细节（详见各 skill 的 references/api-notes.md）：
- 模型始终思考、无法关闭：`reasoning_effort="low"` 实测 reasoning_tokens=0
  （等效 DeepSeek 的关思考），批量/结构化任务用它；深读回答用 "high"。
- reasoning 计入 max_tokens，预算不足会得到空 content + finish=length；
  所有调用默认给足 max_tokens，绝不调小。
- 无 Files API：图片一律 base64 data URL 内联（实测单请求 30 图 OK）。
- 图片按分辨率计费，约 750 像素²/token（900×1273 页图 ≈1500 token）。
"""
import base64
import json
import os
import random
import re
import sys
import time
from pathlib import Path

from openai import OpenAI

BASE_URL = os.environ.get("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
MODEL = os.environ.get("GLM_VISION_MODEL", "glm-5.3-flash")


def _load_api_key() -> str:
    """密钥来源（按优先级）：环境变量 GLM_API_KEY / ZHIPU_API_KEY > ~/.glm_api_key 首行。
    本 skill 会公开分发，密钥绝不能硬编码在代码里。"""
    key = (os.environ.get("GLM_API_KEY") or os.environ.get("ZHIPU_API_KEY") or "").strip()
    if not key:
        kf = Path.home() / ".glm_api_key"
        if kf.is_file():
            key = kf.read_text(encoding="utf-8").strip().splitlines()[0].strip()
    if not key:
        sys.exit("[error] 未找到智谱 API key，二选一：\n"
                 "  1) 设置环境变量 GLM_API_KEY\n"
                 "  2) 把 key 写入 ~/.glm_api_key 文件首行（仅存在于本机，不随 skill 分发）")
    return key


class ChatError(RuntimeError):
    pass


def img_block(path, label=None) -> list:
    """把本地图片变成 image_url 内容块（data URL 内联）。可选前置一个文本标签。"""
    data = Path(path).read_bytes()
    b64 = base64.b64encode(data).decode()
    blocks = []
    if label:
        blocks.append({"type": "text", "text": label})
    blocks.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
    return blocks


def video_block(path, label=None) -> list:
    """把本地视频变成 video_url 内容块（data URL 内联）。

    注意：GLM 单次请求只能传一类非文本模态——视频块不能与图片块混用。
    """
    data = Path(path).read_bytes()
    b64 = base64.b64encode(data).decode()
    blocks = []
    if label:
        blocks.append({"type": "text", "text": label})
    blocks.append({"type": "video_url", "video_url": {"url": f"data:video/mp4;base64,{b64}"}})
    return blocks


def parse_json_lenient(text):
    """解析模型返回的 JSON，容忍代码围栏、None、尾逗号等常见毛病。"""
    if not text or not text.strip():
        raise ChatError("no content to parse")
    s = text.strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*(.+?)\s*```", s, re.DOTALL)
    if m:
        s = m.group(1)
    s = s.strip()
    starts = [i for i in (s.find("{"), s.find("[")) if i != -1]
    if starts:
        s = s[min(starts):]
        for closer in (s.rfind("}"), s.rfind("]")):
            if closer != -1:
                s = s[: closer + 1]
                break
    s = re.sub(r"\bNone\b", "null", s)
    s = re.sub(r",\s*([\]}])", r"\1", s)
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        raise ChatError(f"unparseable JSON: {e}; head={s[:120]!r}")


class GLMClient:
    def __init__(self, api_key=None, base_url=None, model=None):
        self.client = OpenAI(
            api_key=api_key or _load_api_key(),
            base_url=base_url or BASE_URL,
            max_retries=0,  # 重试与退避由本类统一控制
        )
        self.model = model or MODEL

    def chat(self, blocks, system=None, effort="low", json_mode=False,
             max_tokens=16384, temperature=1.0, retries=4, timeout=600):
        """调用 glm-5.3-flash，返回 (text, finish_reason)。

        effort: "low"(批量抽取，实测不产生思考token) / "high"(默认强度) / "max"(深度推理)
        注意模型始终思考且 reasoning 计入 max_tokens，budget 不可调小。
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": blocks})
        kwargs = dict(model=self.model, messages=messages, max_tokens=max_tokens,
                      timeout=timeout, extra_body={"reasoning_effort": effort})
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        delay = 2.0
        last = None
        for attempt in range(1, retries + 1):
            try:
                resp = self.client.chat.completions.create(**kwargs)
                text = (resp.choices[0].message.content or "").strip()
                if not text:
                    last = ChatError(f"empty content (attempt {attempt}, finish="
                                     f"{resp.choices[0].finish_reason})")
                else:
                    return text, (resp.choices[0].finish_reason or "stop")
            except Exception as e:  # 网络 / 429 / 5xx / 超时
                last = e
            if attempt < retries:
                time.sleep(delay + random.random())
                delay = min(delay * 2, 30)
        raise ChatError(f"chat failed after {retries} attempts: {last}")

    def chat_json(self, blocks, **kw):
        text, finish = self.chat(blocks, json_mode=True, **kw)
        return parse_json_lenient(text), finish
