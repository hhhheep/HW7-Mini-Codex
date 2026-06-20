from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModelConfig:
    base_url: str
    api_key: str
    discussion_model: str
    writer_model: str


class ModelClientError(RuntimeError):
    pass


def load_model_config() -> ModelConfig:
    api_key = (
        os.getenv("HW7_LLM_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
        or os.getenv("DASHSCOPE_API_KEY")
        or os.getenv("DEEPSEEK_API_KEY")
        or ""
    ).strip()
    base_url = (
        os.getenv("HW7_LLM_BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or os.getenv("OPENAI_COMPATIBLE_BASE_URL")
        or _default_base_url()
    ).strip()
    discussion_model = (
        os.getenv("HW7_DISCUSSION_MODEL")
        or os.getenv("HW7_LLM_MODEL")
        or _default_model()
    ).strip()
    writer_model = (
        os.getenv("HW7_WRITER_MODEL")
        or os.getenv("HW7_LLM_MODEL")
        or discussion_model
    ).strip()
    if not api_key:
        raise ModelClientError(
            "No API key found. Set HW7_LLM_API_KEY or a provider key such as OPENAI_API_KEY / OPENROUTER_API_KEY."
        )
    if not base_url:
        raise ModelClientError("No base URL configured.")
    if not discussion_model or not writer_model:
        raise ModelClientError("Model names are not configured.")
    return ModelConfig(
        base_url=base_url.rstrip("/"),
        api_key=api_key,
        discussion_model=discussion_model,
        writer_model=writer_model,
    )


def chat_completion(config: ModelConfig, model: str, system_prompt: str, user_prompt: str) -> str:
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{config.base_url}/chat/completions",
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "HW7 Agentic Generative AI Experiment Orchestrator",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise ModelClientError(f"Provider HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise ModelClientError(f"Provider request failed: {exc}") from exc
    loaded = json.loads(raw)
    try:
        content = loaded["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ModelClientError(f"Unexpected provider response shape: {raw[:500]}") from exc
    return str(content).strip()


def _default_base_url() -> str:
    if os.getenv("OPENROUTER_API_KEY"):
        return "https://openrouter.ai/api/v1"
    if os.getenv("DASHSCOPE_API_KEY"):
        return "https://dashscope.aliyuncs.com/compatible-mode/v1"
    if os.getenv("DEEPSEEK_API_KEY"):
        return "https://api.deepseek.com/v1"
    return "https://api.openai.com/v1"


def _default_model() -> str:
    if os.getenv("OPENROUTER_API_KEY"):
        return "openai/gpt-4o-mini"
    if os.getenv("DASHSCOPE_API_KEY"):
        return "qwen-plus"
    if os.getenv("DEEPSEEK_API_KEY"):
        return "deepseek-chat"
    return "gpt-4o-mini"
