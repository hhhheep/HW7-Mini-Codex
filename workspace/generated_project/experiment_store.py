from __future__ import annotations

from datetime import datetime, timezone

# In-memory history store
_history: list[dict[str, str]] = []


def create_record(prompt: str, response: str, model_name: str = "mock-local") -> dict[str, str]:
    record = {
        "prompt": prompt,
        "response": response,
        "model_name": model_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _history.append(record)
    return record


def get_history() -> list[dict[str, str]]:
    """Return the full generation history."""
    return list(_history)


def clear_history() -> None:
    """Clear all records from history."""
    _history.clear()
