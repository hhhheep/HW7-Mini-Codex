from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .agents import (
    architect_api,
    architect_mock,
    coder_api,
    coder_mock,
    coder_repair_api,
    judge_api,
    judge_mock,
    planner_api,
    planner_mock,
)
from .model_client import ModelConfig, load_model_config
from .schemas import AgentOutput, ArchitectureSpec, GeneratedFile, JudgeReport, TaskSpec, ValidationResult


def run_workflow(
    project_idea: str,
    output_dir: Path,
    mode: str = "mock_test",
    model_config: ModelConfig | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    started_at = _utc_now()
    provider: dict[str, str] | None = None

    if mode == "api":
        config = model_config or load_model_config()
        provider = {
            "base_url": config.base_url,
            "discussion_model": config.discussion_model,
            "writer_model": config.writer_model,
        }
        task_spec, planner_output = planner_api(project_idea, config)
        architecture, architect_output = architect_api(task_spec, config)
        generated_files, coder_output = coder_api(task_spec, architecture, config)
    elif mode == "mock_test":
        task_spec, planner_output = planner_mock(project_idea)
        architecture, architect_output = architect_mock(task_spec)
        generated_files, coder_output = coder_mock(task_spec, architecture)
        config = None
    else:
        raise ValueError(f"unsupported mode: {mode}")

    agent_outputs = [planner_output, architect_output, coder_output]
    generated_files = _normalize_generated_files(generated_files)
    generated_root = output_dir / "generated_project"
    _write_generated_files(generated_root, generated_files)
    validations = _run_validations(generated_root)

    if mode == "api" and config is not None and not _validations_pass(validations):
        repaired_files, repair_output = coder_repair_api(
            task_spec,
            architecture,
            generated_files,
            validations,
            config,
        )
        agent_outputs.append(repair_output)
        generated_files = _normalize_generated_files(repaired_files)
        _write_generated_files(generated_root, generated_files)
        validations = _run_validations(generated_root)

    if mode == "api" and config is not None:
        judge_report = judge_api(task_spec, architecture, generated_files, validations, config)
    else:
        judge_report = judge_mock(task_spec, generated_files, validations)

    reporter_output = AgentOutput(
        role="Reporter",
        summary="Collected generated files, validation output, judge result, and final downloadable artifacts.",
        decisions=["Write run.json", "Write WORKFLOW_LOG.md", "Write final_report.md", "Zip generated_project"],
        artifacts_to_create=["run.json", "WORKFLOW_LOG.md", "final_report.md", "generated_project.zip"],
        next_steps=["Record demo video/screenshot and submit repository link."],
    )
    finished_at = _utc_now()
    payload = {
        "schema_version": 2,
        "project_idea": project_idea,
        "started_at": started_at,
        "finished_at": finished_at,
        "mode": mode,
        "api_mode_used": mode == "api",
        "api_packaged": False,
        "provider": provider,
        "task_spec": task_spec.model_dump(),
        "architecture": architecture.model_dump(),
        "agent_outputs": [item.model_dump() for item in agent_outputs],
        "generated_files": [item.model_dump() for item in generated_files],
        "validations": [item.model_dump() for item in validations],
        "judge_report": judge_report.model_dump(),
        "reporter": reporter_output.model_dump(),
        "artifacts": {
            "generated_project_dir": str(generated_root),
            "generated_project_zip": str(output_dir / "generated_project.zip"),
            "workflow_log": str(output_dir / "WORKFLOW_LOG.md"),
            "final_report": str(output_dir / "final_report.md"),
        },
    }
    _write_json(output_dir / "run.json", payload)
    (output_dir / "WORKFLOW_LOG.md").write_text(_render_workflow_log(payload), encoding="utf-8")
    (output_dir / "workflow_log.md").write_text(_render_workflow_log(payload), encoding="utf-8")
    (output_dir / "final_report.md").write_text(_render_final_report(payload), encoding="utf-8")
    (output_dir / "final_package.md").write_text(_render_final_report(payload), encoding="utf-8")
    _zip_dir(generated_root, output_dir / "generated_project.zip")
    return payload


def _write_generated_files(root: Path, files: list[GeneratedFile]) -> None:
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    for generated in files:
        path = (root / generated.path).resolve()
        if root.resolve() not in path.parents and path != root.resolve():
            raise ValueError(f"generated path escapes project root: {generated.path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(generated.content, encoding="utf-8")


def _normalize_generated_files(files: list[GeneratedFile]) -> list[GeneratedFile]:
    normalized: list[GeneratedFile] = []
    for generated in files:
        parts = Path(generated.path).parts
        if parts and parts[0] == "generated_project":
            stripped = Path(*parts[1:]).as_posix()
            normalized.append(generated.model_copy(update={"path": stripped}))
        else:
            normalized.append(generated)
    return normalized


def _validations_pass(validations: list[ValidationResult]) -> bool:
    return bool(validations) and all(result.success for result in validations)


def _run_validations(generated_root: Path) -> list[ValidationResult]:
    generated_arg = generated_root.name
    commands = [
        (
            [sys.executable, "-m", "compileall", generated_arg],
            f"python -m compileall {generated_arg}",
            generated_root.parent,
        ),
    ]
    tests_dir = generated_root / "tests"
    if tests_dir.exists():
        tests_arg = "tests"
        commands.append(
            (
                [sys.executable, "-m", "unittest", "discover", "-s", tests_arg],
                f"python -m unittest discover -s {tests_arg}",
                generated_root,
            )
        )
    results = []
    for command, display_command, cwd in commands:
        completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
        results.append(
            ValidationResult(
                command=display_command,
                success=completed.returncode == 0,
                stdout=completed.stdout,
                stderr=completed.stderr,
                artifacts_found=[str(path.relative_to(generated_root)) for path in generated_root.rglob("*") if path.is_file()],
            )
        )
    return results


def _render_workflow_log(payload: dict[str, Any]) -> str:
    lines = [
        "# Workflow Log",
        "",
        f"- Mode: {payload['mode']}",
        f"- Started: {payload['started_at']}",
        f"- Finished: {payload['finished_at']}",
        "",
        "## User Task",
        "",
        payload["project_idea"].strip(),
        "",
        "## Planner Output",
        "",
        "```json",
        json.dumps(payload["task_spec"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Architect Output",
        "",
        "```json",
        json.dumps(payload["architecture"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Agent Trace",
    ]
    for item in payload["agent_outputs"]:
        lines.extend(["", f"### {item['role']}", "", item["summary"], ""])
        if item.get("prompt"):
            lines.extend(["Prompt:", "", "```text", item["prompt"], "```"])
        if item.get("raw_response"):
            lines.extend(["Raw response:", "", "```text", item["raw_response"], "```"])
    lines.extend(["", "## Validation Results", ""])
    for result in payload["validations"]:
        lines.extend(
            [
                f"### `{result['command']}`",
                "",
                f"Success: `{result['success']}`",
                "",
                "Stdout:",
                "",
                "```text",
                result.get("stdout", ""),
                "```",
                "",
                "Stderr:",
                "",
                "```text",
                result.get("stderr", ""),
                "```",
            ]
        )
    lines.extend(
        [
            "",
            "## Judge Report",
            "",
            "```json",
            json.dumps(payload["judge_report"], indent=2, ensure_ascii=False),
            "```",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _render_final_report(payload: dict[str, Any]) -> str:
    judge = payload["judge_report"]
    generated_paths = [item["path"] for item in payload["generated_files"]]
    validation_lines = [
        f"- `{item['command']}` -> {'passed' if item['success'] else 'failed'}"
        for item in payload["validations"]
    ]
    return "\n".join(
        [
            "# Final Report",
            "",
            "## Project",
            "",
            payload["task_spec"]["title"],
            "",
            "## Objective",
            "",
            payload["task_spec"]["objective"],
            "",
            "## Generated Files",
            "",
            *[f"- `{path}`" for path in generated_paths],
            "",
            "## Validation",
            "",
            *validation_lines,
            "",
            "## Judge",
            "",
            f"Pass status: `{judge['pass_status']}`",
            "",
            judge["final_summary"],
            "",
            "## Artifacts",
            "",
            "- `generated_project/`",
            "- `generated_project.zip`",
            "- `WORKFLOW_LOG.md`",
            "- `final_report.md`",
        ]
    ).rstrip() + "\n"


def _zip_dir(source: Path, target: Path) -> None:
    if target.exists():
        target.unlink()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in source.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                archive.write(path, path.relative_to(source).as_posix())


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
