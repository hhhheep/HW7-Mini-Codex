from __future__ import annotations

import csv
import difflib
import hashlib
import io
import json
import shutil
import subprocess
import sys
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from .model_client import ModelConfig, chat_completion, load_model_config
from .schemas import ValidationResult


DEFAULT_WORKSPACE = Path("workspace/generated_project")
ALLOWED_SUFFIXES = {".py", ".md", ".txt", ".html", ".css", ".js", ".json", ".toml", ".yaml", ".yml", ".csv"}
IGNORED_PARTS = {"__pycache__", ".pytest_cache", ".streamlit"}


class FileSnapshot(BaseModel):
    path: str
    sha256: str
    content: str


class ContextPack(BaseModel):
    workspace_path: str
    selected_files: list[FileSnapshot] = Field(default_factory=list)
    rejected_files: list[dict[str, str]] = Field(default_factory=list)
    project_summary: str


class FileReplacement(BaseModel):
    path: str
    old_content_hash: str | None = None
    new_content: str
    reason: str


class CodeChangeSet(BaseModel):
    change_id: str
    summary: str
    user_intent: str
    files: list[FileReplacement]
    expected_visible_change: str
    validation_commands: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    prompt: str = ""
    raw_response: str = ""


class ApplyResult(BaseModel):
    status: str
    applied_files: list[str] = Field(default_factory=list)
    rejected_files: list[dict[str, str]] = Field(default_factory=list)
    backup_dir: str = ""
    validations: list[ValidationResult] = Field(default_factory=list)
    preview_url: str = ""


def ensure_sample_workspace(workspace_root: Path, reset: bool = False) -> None:
    if reset and workspace_root.exists():
        shutil.rmtree(workspace_root)
    workspace_root.mkdir(parents=True, exist_ok=True)
    for rel_path, content in _base_workspace_files().items():
        target = workspace_root / rel_path
        if target.exists() and not reset:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")


def collect_context(workspace_root: Path) -> ContextPack:
    workspace_root = workspace_root.resolve()
    selected: list[FileSnapshot] = []
    rejected: list[dict[str, str]] = []
    for path in sorted(workspace_root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(workspace_root).as_posix()
        if any(part in IGNORED_PARTS for part in path.relative_to(workspace_root).parts):
            rejected.append({"path": rel, "reason": "ignored generated/cache path"})
            continue
        if path.suffix.lower() not in ALLOWED_SUFFIXES:
            rejected.append({"path": rel, "reason": "unsupported file type"})
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        selected.append(FileSnapshot(path=rel, sha256=_sha256_text(text), content=text))
    return ContextPack(
        workspace_path=str(workspace_root),
        selected_files=selected,
        rejected_files=rejected,
        project_summary=_summarize_files(selected),
    )


def propose_changes(
    user_message: str,
    workspace_root: Path,
    output_dir: Path,
    mode: str = "mock_test",
    model_config: ModelConfig | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    context = collect_context(workspace_root)
    if mode == "api":
        config = model_config or load_model_config()
        changeset = _api_changeset(user_message, context, config)
        provider = {
            "base_url": config.base_url,
            "discussion_model": config.discussion_model,
            "writer_model": config.writer_model,
        }
    elif mode == "mock_test":
        changeset = _mock_changeset(user_message, context)
        provider = None
    else:
        raise ValueError(f"unsupported mode: {mode}")
    changeset = _normalize_changeset(changeset)
    payload = {
        "schema_version": 3,
        "kind": "mini_codex_proposal",
        "created_at": _utc_now(),
        "mode": mode,
        "api_mode_used": mode == "api",
        "provider": provider,
        "user_message": user_message,
        "context": context.model_dump(),
        "changeset": changeset.model_dump(),
        "diffs": render_diffs(changeset, context),
    }
    _write_json(output_dir / "proposal.json", payload)
    (output_dir / "WORKFLOW_LOG.md").write_text(_render_proposal_log(payload), encoding="utf-8")
    return payload


def apply_changeset(
    changeset_payload: dict[str, Any] | CodeChangeSet,
    workspace_root: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    changeset = (
        changeset_payload
        if isinstance(changeset_payload, CodeChangeSet)
        else CodeChangeSet.model_validate(changeset_payload)
    )
    workspace_root = workspace_root.resolve()
    backup_dir = output_dir / "snapshots" / f"before_{changeset.change_id}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    applied: list[str] = []
    rejected: list[dict[str, str]] = []

    for replacement in changeset.files:
        target = _safe_workspace_path(workspace_root, replacement.path)
        current = target.read_text(encoding="utf-8", errors="replace") if target.exists() else ""
        current_hash = _sha256_text(current) if target.exists() else None
        if replacement.old_content_hash and current_hash != replacement.old_content_hash:
            rejected.append(
                {
                    "path": replacement.path,
                    "reason": "old_content_hash mismatch",
                    "expected": replacement.old_content_hash,
                    "actual": current_hash or "<missing>",
                }
            )
            continue
        if target.exists():
            backup = backup_dir / replacement.path
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_text(current, encoding="utf-8", newline="\n")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(replacement.new_content, encoding="utf-8", newline="\n")
        applied.append(replacement.path)

    validations = validate_workspace(workspace_root)
    result = ApplyResult(
        status="applied" if applied and not rejected else "partial" if applied else "rejected",
        applied_files=applied,
        rejected_files=rejected,
        backup_dir=str(backup_dir),
        validations=validations,
    )
    payload = {
        "schema_version": 3,
        "kind": "mini_codex_apply",
        "created_at": _utc_now(),
        "changeset": changeset.model_dump(),
        "result": result.model_dump(),
    }
    _write_json(output_dir / "apply_result.json", payload)
    existing_log = (output_dir / "WORKFLOW_LOG.md").read_text(encoding="utf-8") if (output_dir / "WORKFLOW_LOG.md").exists() else ""
    (output_dir / "WORKFLOW_LOG.md").write_text(existing_log + "\n" + _render_apply_log(payload), encoding="utf-8")
    return payload


def restore_changeset_snapshot(apply_payload: dict[str, Any], workspace_root: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    workspace_root = workspace_root.resolve()
    result = apply_payload.get("result", {})
    backup_dir = Path(result.get("backup_dir", "")).resolve()
    restored: list[str] = []
    removed: list[str] = []
    rejected: list[dict[str, str]] = []

    for path in result.get("applied_files", []):
        target = _safe_workspace_path(workspace_root, path)
        backup = backup_dir / path
        if backup.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(backup.read_text(encoding="utf-8", errors="replace"), encoding="utf-8", newline="\n")
            restored.append(path)
        elif target.exists():
            target.unlink()
            removed.append(path)
        else:
            rejected.append({"path": path, "reason": "target and backup are both missing"})

    validations = validate_workspace(workspace_root)
    payload = {
        "schema_version": 1,
        "kind": "mini_codex_restore",
        "created_at": _utc_now(),
        "restored_files": restored,
        "removed_files": removed,
        "rejected_files": rejected,
        "validations": [item.model_dump() for item in validations],
    }
    _write_json(output_dir / "restore_result.json", payload)
    existing_log = (output_dir / "WORKFLOW_LOG.md").read_text(encoding="utf-8") if (output_dir / "WORKFLOW_LOG.md").exists() else ""
    (output_dir / "WORKFLOW_LOG.md").write_text(existing_log + "\n" + _render_restore_log(payload), encoding="utf-8")
    return payload


def validate_workspace(workspace_root: Path) -> list[ValidationResult]:
    workspace_root = workspace_root.resolve()
    project_root = workspace_root.parents[1] if workspace_root.parent.name == "workspace" else workspace_root.parent
    workspace_arg = workspace_root.relative_to(project_root).as_posix()
    commands: list[tuple[list[str], str, Path]] = [
        (
            [sys.executable, "-m", "compileall", workspace_arg],
            f"python -m compileall {workspace_arg}",
            project_root,
        )
    ]
    tests_dir = workspace_root / "tests"
    if tests_dir.exists():
        commands.append(
            (
                [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                "python -m unittest discover -s tests",
                workspace_root,
            )
        )
    results: list[ValidationResult] = []
    for command, display_command, cwd in commands:
        started = time.perf_counter()
        completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
        duration = time.perf_counter() - started
        stdout = completed.stdout
        if stdout:
            stdout += f"\n[duration_seconds={duration:.3f}]"
        else:
            stdout = f"[duration_seconds={duration:.3f}]"
        results.append(
            ValidationResult(
                command=display_command,
                success=completed.returncode == 0,
                stdout=stdout,
                stderr=completed.stderr,
                artifacts_found=[
                    str(path.relative_to(workspace_root)).replace("\\", "/")
                    for path in workspace_root.rglob("*")
                    if path.is_file() and "__pycache__" not in path.parts
                ],
            )
        )
    return results


def render_diffs(changeset: CodeChangeSet, context: ContextPack) -> list[dict[str, str]]:
    old_by_path = {item.path: item.content for item in context.selected_files}
    diffs: list[dict[str, str]] = []
    for replacement in changeset.files:
        old_text = old_by_path.get(replacement.path, "")
        diff = "\n".join(
            difflib.unified_diff(
                old_text.splitlines(),
                replacement.new_content.splitlines(),
                fromfile=f"a/{replacement.path}",
                tofile=f"b/{replacement.path}",
                lineterm="",
            )
        )
        diffs.append({"path": replacement.path, "reason": replacement.reason, "diff": diff})
    return diffs


def launch_preview(workspace_root: Path, output_dir: Path, port: int = 8502) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    workspace_root = workspace_root.resolve()
    log_path = output_dir / "preview_streamlit.log"
    app_path = workspace_root / "app.py"
    index_path = workspace_root / "index.html"
    if app_path.exists():
        command = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(app_path),
            "--server.port",
            str(port),
            "--server.headless",
            "true",
        ]
        url = f"http://localhost:{port}"
        preview_type = "streamlit"
    elif index_path.exists():
        command = [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"]
        url = f"http://localhost:{port}/index.html"
        preview_type = "static"
    else:
        raise ValueError("No preview entry found. Add app.py for Streamlit or index.html for a static site.")
    with log_path.open("ab") as log:
        process = subprocess.Popen(
            command,
            cwd=workspace_root,
            stdout=log,
            stderr=log,
        )
    return {"url": url, "pid": process.pid, "log": str(log_path), "type": preview_type}


def zip_workspace(workspace_root: Path, output_dir: Path, filename: str = "current_workspace.zip") -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / filename
    if zip_path.exists():
        zip_path.unlink()
    workspace_root = workspace_root.resolve()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(workspace_root.rglob("*")):
            if not path.is_file():
                continue
            rel_parts = path.relative_to(workspace_root).parts
            if any(part in IGNORED_PARTS for part in rel_parts):
                continue
            if path.suffix.lower() in {".pyc", ".pyo", ".log"}:
                continue
            archive.write(path, path.relative_to(workspace_root).as_posix())
    return zip_path


def _api_changeset(user_message: str, context: ContextPack, config: ModelConfig) -> CodeChangeSet:
    prompt = """You are the Code Patch Agent for a small Mini-Codex homework demo.
Return only JSON matching this schema:
{
  "change_id": "short stable id",
  "summary": "human readable summary",
  "user_intent": "what the user asked for",
  "files": [
    {
      "path": "relative/path.py",
      "old_content_hash": "sha256 copied from context",
      "new_content": "full replacement file content",
      "reason": "why this file changes"
    }
  ],
  "expected_visible_change": "what the preview app should show",
  "validation_commands": ["python -m compileall workspace/generated_project", "python -m unittest discover -s workspace/generated_project/tests"],
  "risks": ["risk strings"]
}

Rules:
- Generate full-file replacements, not partial patches.
- Modify only files already present in the context unless the user explicitly asks for a new file.
- Keep tests offline: no network access and no API keys.
- Do not hardcode credentials.
- Keep the Streamlit app runnable on a local machine."""
    raw = chat_completion(
        config,
        config.writer_model,
        prompt,
        json.dumps({"user_request": user_message, "context": context.model_dump()}, ensure_ascii=False, indent=2),
    )
    try:
        changeset = CodeChangeSet.model_validate_json(_extract_json(raw))
    except ValidationError as exc:
        repair_prompt = f"Your previous response failed schema validation: {exc}. Return only valid JSON."
        repaired = chat_completion(config, config.writer_model, repair_prompt, raw)
        changeset = CodeChangeSet.model_validate_json(_extract_json(repaired))
        raw = repaired
    return changeset.model_copy(update={"prompt": prompt, "raw_response": raw})


def _mock_changeset(user_message: str, context: ContextPack) -> CodeChangeSet:
    if not context.selected_files:
        return _mock_new_project_changeset(user_message, context)
    files = _workspace_versions("csv" if "csv" in user_message.lower() or "export" in user_message.lower() else "classroom" if "classroom" in user_message.lower() or "ui" in user_message.lower() else "history")
    old_hash = {item.path: item.sha256 for item in context.selected_files}
    replacements: list[FileReplacement] = []
    if "csv" in user_message.lower() or "export" in user_message.lower():
        target_paths = ["app.py", "experiment_store.py", "tests/test_basic.py"]
        summary = "Add CSV export support for generation history."
        expected = "The preview app includes a CSV download button for prompt/response history."
    elif "classroom" in user_message.lower() or "ui" in user_message.lower():
        target_paths = ["app.py", "README.md"]
        summary = "Make the demo UI more classroom friendly."
        expected = "The preview app has clearer labels, title, and classroom-demo framing."
    else:
        target_paths = ["app.py", "experiment_store.py", "tests/test_basic.py"]
        summary = "Add generation history table."
        expected = "The preview app shows a table of prompts, responses, and timestamps."
    for path in target_paths:
        replacements.append(
            FileReplacement(
                path=path,
                old_content_hash=old_hash.get(path),
                new_content=files[path],
                reason=f"Implement request: {summary}",
            )
        )
    return CodeChangeSet(
        change_id=f"mock_{uuid.uuid4().hex[:8]}",
        summary=summary,
        user_intent=user_message,
        files=replacements,
        expected_visible_change=expected,
        validation_commands=[
            "python -m compileall workspace/generated_project",
            "python -m unittest discover -s workspace/generated_project/tests",
        ],
        risks=["Mock mode is deterministic evidence, not a live model-backed patch."],
    )


def _mock_new_project_changeset(user_message: str, context: ContextPack) -> CodeChangeSet:
    lowered = user_message.lower()
    if "html" in lowered or "website" in lowered or "static" in lowered:
        files = _static_site_files(user_message)
        summary = "Create a static website project."
        expected = "The workspace contains an index.html static site that can be previewed locally."
    elif "cli" in lowered or "command" in lowered:
        files = _cli_project_files(user_message)
        summary = "Create a Python CLI project."
        expected = "The workspace contains a runnable Python CLI module and offline tests."
    else:
        files = _minimal_python_project_files(user_message)
        summary = "Create a minimal Python project."
        expected = "The workspace contains Python source, README, and offline tests."
    replacements = [
        FileReplacement(
            path=path,
            old_content_hash=None,
            new_content=content,
            reason=f"Create new file for request: {summary}",
        )
        for path, content in files.items()
    ]
    return CodeChangeSet(
        change_id=f"mock_{uuid.uuid4().hex[:8]}",
        summary=summary,
        user_intent=user_message,
        files=replacements,
        expected_visible_change=expected,
        validation_commands=[
            f"python -m compileall {context.workspace_path}",
            "python -m unittest discover -s tests",
        ],
        risks=["Mock mode is deterministic evidence, not a live model-backed patch."],
    )


def _normalize_changeset(changeset: CodeChangeSet) -> CodeChangeSet:
    if changeset.validation_commands:
        return changeset
    return changeset.model_copy(
        update={
            "validation_commands": [
                "python -m compileall workspace/generated_project",
                "python -m unittest discover -s workspace/generated_project/tests",
            ]
        }
    )


def _safe_workspace_path(workspace_root: Path, rel_path: str) -> Path:
    normalized = rel_path.replace("\\", "/").lstrip("/")
    target = (workspace_root / normalized).resolve()
    if target != workspace_root and workspace_root not in target.parents:
        raise ValueError(f"path escapes workspace: {rel_path}")
    return target


def _summarize_files(files: list[FileSnapshot]) -> str:
    if not files:
        return "No editable files found."
    return "Editable workspace files: " + ", ".join(f"{item.path} ({item.sha256[:8]})" for item in files)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _extract_json(raw: str) -> str:
    stripped = raw.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    first_obj = stripped.find("{")
    last_obj = stripped.rfind("}")
    if first_obj >= 0 and last_obj > first_obj:
        return stripped[first_obj : last_obj + 1]
    return stripped


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _render_proposal_log(payload: dict[str, Any]) -> str:
    changeset = payload["changeset"]
    lines = [
        "# Mini-Codex Workflow Log",
        "",
        f"- Created: {payload['created_at']}",
        f"- Mode: {payload['mode']}",
        f"- User request: {payload['user_message']}",
        "",
        "## Selected Files",
    ]
    for item in payload["context"]["selected_files"]:
        lines.append(f"- `{item['path']}` sha256 `{item['sha256']}`")
    lines.extend(["", "## Proposed Change", "", changeset["summary"], "", "## Files"])
    for item in changeset["files"]:
        lines.append(f"- `{item['path']}`: {item['reason']}")
    lines.extend(["", "## Diffs"])
    for item in payload["diffs"]:
        lines.extend(["", f"### {item['path']}", "", "```diff", item["diff"], "```"])
    if changeset.get("prompt"):
        lines.extend(["", "## Raw Model Prompt", "", "```text", changeset["prompt"], "```"])
    if changeset.get("raw_response"):
        lines.extend(["", "## Raw Model Response", "", "```text", changeset["raw_response"], "```"])
    return "\n".join(lines).rstrip() + "\n"


def _render_apply_log(payload: dict[str, Any]) -> str:
    result = payload["result"]
    lines = ["", "## Apply Decision", "", f"- Status: {result['status']}"]
    for path in result["applied_files"]:
        lines.append(f"- Applied: `{path}`")
    for item in result["rejected_files"]:
        lines.append(f"- Rejected: `{item['path']}` ({item['reason']})")
    lines.extend(["", "## Validation"])
    for validation in result["validations"]:
        lines.append(f"- `{validation['command']}` -> `{validation['success']}`")
    return "\n".join(lines).rstrip() + "\n"


def _render_restore_log(payload: dict[str, Any]) -> str:
    lines = ["", "## Restore Decision", "", f"- Created: {payload['created_at']}"]
    for path in payload["restored_files"]:
        lines.append(f"- Restored: `{path}`")
    for path in payload["removed_files"]:
        lines.append(f"- Removed new file: `{path}`")
    for item in payload["rejected_files"]:
        lines.append(f"- Rejected: `{item['path']}` ({item['reason']})")
    lines.extend(["", "## Restore Validation"])
    for validation in payload["validations"]:
        lines.append(f"- `{validation['command']}` -> `{validation['success']}`")
    return "\n".join(lines).rstrip() + "\n"


def _base_workspace_files() -> dict[str, str]:
    return _workspace_versions("base")


def _workspace_versions(version: str) -> dict[str, str]:
    include_history = version in {"history", "csv", "classroom"}
    include_csv = version in {"csv"}
    classroom = version == "classroom"
    return {
        "app.py": _app_py(include_history=include_history, include_csv=include_csv, classroom=classroom),
        "llm_client.py": _llm_client_py(),
        "experiment_store.py": _experiment_store_py(include_history=include_history, include_csv=include_csv),
        "README.md": _readme_md(include_history=include_history, include_csv=include_csv, classroom=classroom),
        "tests/test_basic.py": _test_basic_py(include_history=include_history, include_csv=include_csv),
    }


def _minimal_python_project_files(user_message: str) -> dict[str, str]:
    return {
        "main.py": """from __future__ import annotations


def summarize_task(task: str) -> str:
    normalized = " ".join(task.strip().split()) or "empty task"
    return f"Mini-Codex project task: {normalized}"


if __name__ == "__main__":
    print(summarize_task("Create a local project from an empty workspace."))
""",
        "README.md": f"""# Mini-Codex Generated Python Project

Created from an empty workspace.

Original request:

```text
{user_message.strip()}
```

## Run

```powershell
python main.py
```

## Test

```powershell
python -m unittest discover -s tests
```
""",
        "tests/test_basic.py": """from __future__ import annotations

import unittest

from main import summarize_task


class GeneratedProjectTest(unittest.TestCase):
    def test_summarize_task_includes_input(self) -> None:
        self.assertIn("hello", summarize_task("hello"))


if __name__ == "__main__":
    unittest.main()
""",
    }


def _cli_project_files(user_message: str) -> dict[str, str]:
    files = _minimal_python_project_files(user_message)
    files["main.py"] = """from __future__ import annotations

import argparse


def build_message(name: str, excited: bool = False) -> str:
    suffix = "!" if excited else "."
    return f"Hello, {name}{suffix}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Mini-Codex generated CLI")
    parser.add_argument("name", nargs="?", default="student")
    parser.add_argument("--excited", action="store_true")
    args = parser.parse_args()
    print(build_message(args.name, excited=args.excited))


if __name__ == "__main__":
    main()
"""
    files["tests/test_basic.py"] = """from __future__ import annotations

import unittest

from main import build_message


class GeneratedCliTest(unittest.TestCase):
    def test_build_message(self) -> None:
        self.assertEqual(build_message("Ada"), "Hello, Ada.")
        self.assertEqual(build_message("Ada", excited=True), "Hello, Ada!")


if __name__ == "__main__":
    unittest.main()
"""
    return files


def _static_site_files(user_message: str) -> dict[str, str]:
    return {
        "index.html": f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mini-Codex Static Project</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <main>
    <h1>Mini-Codex Static Project</h1>
    <p id="request">{user_message.strip()}</p>
    <button id="action">Mark ready</button>
    <p id="status">Waiting for interaction.</p>
  </main>
  <script src="script.js"></script>
</body>
</html>
""",
        "style.css": """body {
  font-family: Arial, sans-serif;
  margin: 0;
  background: #f7f7f2;
  color: #202124;
}

main {
  max-width: 760px;
  margin: 48px auto;
  padding: 24px;
  border: 1px solid #d8d8d0;
  background: white;
}

button {
  padding: 8px 12px;
}
""",
        "script.js": """const button = document.querySelector("#action");
const status = document.querySelector("#status");

button.addEventListener("click", () => {
  status.textContent = "Static project is ready.";
});
""",
        "README.md": """# Mini-Codex Static Project

Created from an empty workspace.

## Preview

Open `index.html` or use the Mini-Codex preview launcher.
""",
    }


def _app_py(include_history: bool, include_csv: bool, classroom: bool) -> str:
    title = "Classroom LLM Response Lab" if classroom else "Mini LLM Demo"
    intro = (
        "Use this classroom demo to compare a prompt, a deterministic fallback, and the recorded generation history."
        if classroom
        else "Enter a task and generate a mock or API-backed LLM response."
    )
    history_import = ", add_record, history_to_table" + (", history_to_csv" if include_csv else "") if include_history else ""
    history_block = ""
    if include_history:
        history_block = '''
if "history" not in st.session_state:
    st.session_state["history"] = []

if generate:
    st.session_state["history"] = add_record(st.session_state["history"], prompt, response)

st.subheader("Generation history")
rows = history_to_table(st.session_state["history"])
if rows:
    st.dataframe(rows, use_container_width=True)
else:
    st.caption("No generations yet.")
'''
        if include_csv:
            history_block += '''
csv_bytes = history_to_csv(st.session_state["history"])
st.download_button(
    "Download history CSV",
    data=csv_bytes,
    file_name="generation_history.csv",
    mime="text/csv",
    disabled=not bool(st.session_state["history"]),
)
'''
    return f'''from __future__ import annotations

import streamlit as st

from experiment_store import create_record{history_import}
from llm_client import generate_response


st.set_page_config(page_title="{title}", layout="wide")
st.title("{title}")
st.write("{intro}")

prompt = st.text_area("Task prompt", "Explain what an LLM agent does in one paragraph.")
model_name = st.text_input("Model name", "mock-local")
temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.1)
generate = st.button("Generate response")

response = ""
if generate:
    response = generate_response(prompt, model_name=model_name, temperature=temperature)
    st.subheader("Latest response")
    st.write(response)
else:
    st.info("Enter a task and click Generate response.")

latest_record = create_record(prompt, response, model_name=model_name)
st.caption(f"Current record model: {{latest_record['model_name']}}")
{history_block}
'''


def _llm_client_py() -> str:
    return '''from __future__ import annotations

import hashlib


def generate_response(prompt: str, model_name: str = "mock-local", temperature: float = 0.2) -> str:
    """Return a deterministic local response for tests and no-key demos."""
    normalized = " ".join(prompt.strip().split()) or "empty prompt"
    digest = hashlib.sha256(f"{normalized}|{model_name}|{temperature}".encode("utf-8")).hexdigest()[:10]
    return f"[{model_name}] Response {digest}: {normalized}"
'''


def _experiment_store_py(include_history: bool, include_csv: bool) -> str:
    csv_part = ""
    if include_csv:
        csv_part = '''

def history_to_csv(history: list[dict[str, str]]) -> bytes:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["prompt", "response", "model_name", "created_at"])
    writer.writeheader()
    for row in history:
        writer.writerow({
            "prompt": row.get("prompt", ""),
            "response": row.get("response", ""),
            "model_name": row.get("model_name", ""),
            "created_at": row.get("created_at", ""),
        })
    return output.getvalue().encode("utf-8")
'''
    imports = "import csv\nimport io\n" if include_csv else ""
    history_part = ""
    if include_history:
        history_part = '''

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
''' + csv_part
    return f'''from __future__ import annotations

{imports}from datetime import datetime, timezone


def create_record(prompt: str, response: str, model_name: str = "mock-local") -> dict[str, str]:
    return {{
        "prompt": prompt,
        "response": response,
        "model_name": model_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }}
{history_part}
'''


def _readme_md(include_history: bool, include_csv: bool, classroom: bool) -> str:
    features = ["- Generate a deterministic local LLM-style response"]
    if include_history:
        features.append("- Record prompt/response history in the Streamlit session")
    if include_csv:
        features.append("- Export generation history as CSV")
    if classroom:
        features.append("- Present the app with classroom-friendly labels")
    return f'''# Mini LLM Demo Workspace

This is the editable sample project used by the Mini-Codex workbench.

## Features

{chr(10).join(features)}

## Run

```powershell
streamlit run app.py
```

## Test

```powershell
python -m unittest discover -s tests
```
'''


def _test_basic_py(include_history: bool, include_csv: bool) -> str:
    extra_import = ", add_record, history_to_table" + (", history_to_csv" if include_csv else "") if include_history else ""
    history_tests = ""
    if include_history:
        history_tests = '''
    def test_history_records_prompt_and_response(self) -> None:
        rows = add_record([], "prompt", "response", model_name="mock")
        table = history_to_table(rows)
        self.assertEqual(table[0]["prompt"], "prompt")
        self.assertEqual(table[0]["response"], "response")
'''
    if include_csv:
        history_tests += '''
    def test_history_csv_has_headers(self) -> None:
        rows = add_record([], "prompt", "response", model_name="mock")
        text = history_to_csv(rows).decode("utf-8")
        self.assertIn("prompt,response,model_name,created_at", text.splitlines()[0])
        self.assertIn("prompt", text)
'''
    return f'''from __future__ import annotations

import unittest

from experiment_store import create_record{extra_import}
from llm_client import generate_response


class WorkspaceTest(unittest.TestCase):
    def test_mock_response_is_deterministic(self) -> None:
        first = generate_response("hello", model_name="mock", temperature=0.2)
        second = generate_response("hello", model_name="mock", temperature=0.2)
        self.assertEqual(first, second)

    def test_create_record_keeps_prompt_response_and_model(self) -> None:
        record = create_record("prompt", "response", model_name="mock")
        self.assertEqual(record["prompt"], "prompt")
        self.assertEqual(record["response"], "response")
        self.assertEqual(record["model_name"], "mock")
{history_tests}

if __name__ == "__main__":
    unittest.main()
'''
