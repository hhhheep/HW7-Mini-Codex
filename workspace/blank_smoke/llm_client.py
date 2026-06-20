from __future__ import annotations

import hashlib


def generate_response(prompt: str, model_name: str = "mock-local", temperature: float = 0.2) -> str:
    normalized = " ".join(prompt.strip().split()) or "empty prompt"
    digest = hashlib.sha256(f"{normalized}|{model_name}|{temperature}".encode("utf-8")).hexdigest()[:10]
    return f"[{model_name}] Response {digest}: {normalized}"
