from __future__ import annotations

from datetime import datetime, timezone


def create_record(prompt: str, response: str, model_name: str = "mock-local") -> dict[str, str]:
    return {
        "prompt": prompt,
        "response": response,
        "model_name": model_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def add_record(history: list[dict[str, str]], prompt: str, response: str, model_name: str = "mock-local") -> list[dict[str, str]]:
    if not response:
        return list(history)
    return [*history, create_record(prompt, response, model_name=model_name)]


def history_to_table(history: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "prompt": item.get("prompt", ""),
            "response": item.get("response", ""),
            "model_name": item.get("model_name", ""),
            "created_at": item.get("created_at", ""),
        }
        for item in history
    ]

