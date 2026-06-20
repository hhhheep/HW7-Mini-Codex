from __future__ import annotations

from datetime import datetime, timezone


def create_record(prompt: str, response: str, model_name: str = "mock-local") -> dict[str, str]:
    return {
        "prompt": prompt,
        "response": response,
        "model_name": model_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

