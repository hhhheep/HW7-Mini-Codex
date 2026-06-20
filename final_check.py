from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent

REQUIRED_FILES = [
    "README.md",
    "WORKFLOW_LOG.md",
    "AGENT_ASSIGNMENT.md",
    "ASSIGNMENT_REQUIREMENTS_MAP.md",
    "PROJECT_STATUS.md",
    "QA_CHECKLIST.md",
    "DEMO_SCRIPT.md",
    "API_TESTING.md",
    "requirements.txt",
    "app.py",
    "start_demo.py",
    "run_council.py",
    "final_check.py",
    "create_submission_txt.py",
    "create_submission_package.py",
    ".streamlit/config.toml",
    "scripts/run_checks.ps1",
    "scripts/start_app.ps1",
    "scripts/build_package.ps1",
    "demo_materials/README.md",
    "examples/project_idea.txt",
    "examples/live_api_idea.txt",
    "assignment_core/__init__.py",
    "assignment_core/agents.py",
    "assignment_core/model_client.py",
    "assignment_core/runner.py",
    "assignment_core/schemas.py",
    "assignment_core/workbench.py",
    "tests/test_runner.py",
    "tests/test_workbench.py",
    "outputs/workbench_latest/proposal.json",
    "outputs/workbench_latest/apply_result.json",
    "outputs/workbench_latest/WORKFLOW_LOG.md",
    "outputs/workbench_latest/current_workspace.zip",
    "workspace/generated_project/app.py",
    "workspace/generated_project/experiment_store.py",
    "workspace/generated_project/llm_client.py",
    "workspace/generated_project/README.md",
    "workspace/generated_project/tests/test_basic.py",
]

FORBIDDEN_PATTERNS = [
    r"(api[_-]?key|client_secret|password|token)\s*[:=]\s*['\"]?(?!<)[A-Za-z0-9_\-]{20,}",
    r"\bB14\b",
    r"\bNCKU\b",
]


def main() -> int:
    failures: list[str] = []
    failures.extend(_check_required_files())
    failures.extend(_check_workbench_output("outputs/workbench_latest", require_live=False))
    failures.extend(_check_optional_workbench_live())
    failures.extend(_check_optional_orchestrator_run("outputs/demo_run/run.json", require_live=False))
    failures.extend(_check_optional_orchestrator_run("outputs/live_api_run/run.json", require_live=True))
    failures.extend(_check_forbidden_content())
    failures.extend(_run_command([sys.executable, "-m", "py_compile", "app.py", "run_council.py"]))
    failures.extend(_run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests"]))
    failures.extend(_run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=ROOT / "workspace/generated_project"))

    if failures:
        print("FINAL CHECK FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("FINAL CHECK PASSED")
    print("Remaining manual items: student ID, public repo/share link, and demo screenshot/video.")
    return 0


def _check_required_files() -> list[str]:
    return [f"missing required file: {rel}" for rel in REQUIRED_FILES if not (ROOT / rel).exists()]


def _check_workbench_output(rel_dir: str, require_live: bool) -> list[str]:
    root = ROOT / rel_dir
    proposal_path = root / "proposal.json"
    apply_path = root / "apply_result.json"
    failures = []
    if not proposal_path.exists():
        failures.append(f"missing {rel_dir}/proposal.json")
    if not apply_path.exists():
        failures.append(f"missing {rel_dir}/apply_result.json")
    if failures:
        return failures
    try:
        proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid {rel_dir}/proposal.json: {exc}"]
    try:
        apply_payload = json.loads(apply_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid {rel_dir}/apply_result.json: {exc}"]

    if proposal.get("kind") != "mini_codex_proposal":
        failures.append(f"{rel_dir}/proposal.json kind must be mini_codex_proposal")
    if apply_payload.get("kind") != "mini_codex_apply":
        failures.append(f"{rel_dir}/apply_result.json kind must be mini_codex_apply")
    if apply_payload.get("result", {}).get("status") != "applied":
        failures.append(f"{rel_dir}/apply_result result.status must be applied")
    validations = apply_payload.get("result", {}).get("validations", [])
    if not validations or not all(item.get("success") for item in validations):
        failures.append(f"{rel_dir}/apply_result validations must all pass")
    if not proposal.get("diffs"):
        failures.append(f"{rel_dir}/proposal.json must include diffs")
    if require_live:
        if proposal.get("mode") != "api" or proposal.get("api_mode_used") is not True:
            failures.append(f"{rel_dir}/proposal.json must be a Live API run")
        provider = proposal.get("provider")
        if not isinstance(provider, dict) or not provider.get("base_url") or not provider.get("writer_model"):
            failures.append(f"{rel_dir}/proposal.json provider metadata missing")
        if "api_key" in json.dumps(provider or {}, ensure_ascii=False).lower():
            failures.append(f"{rel_dir}/proposal.json provider must not include API keys")
        changeset = proposal.get("changeset", {})
        if not changeset.get("prompt") or not changeset.get("raw_response"):
            failures.append(f"{rel_dir}/proposal.json missing prompt/raw_response evidence")
    return failures


def _check_optional_workbench_live() -> list[str]:
    live_dir = ROOT / "outputs/workbench_live"
    if not live_dir.exists():
        return []
    if not (live_dir / "proposal.json").exists() and not (live_dir / "apply_result.json").exists():
        return []
    return _check_workbench_output("outputs/workbench_live", require_live=True)


def _check_optional_orchestrator_run(rel_path: str, require_live: bool) -> list[str]:
    path = ROOT / rel_path
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid {rel_path}: {exc}"]
    failures = []
    expected_mode = "api" if require_live else "mock_test"
    label = "live auxiliary run" if require_live else "mock auxiliary run"
    if payload.get("mode") != expected_mode:
        failures.append(f"{label} mode is not {expected_mode}")
    if payload.get("api_packaged") is not False:
        failures.append(f"{label} api_packaged must be false")
    if len(payload.get("agent_outputs", [])) < 3:
        failures.append(f"{label} must contain planner/architect/coder agent outputs")
    for key in ("task_spec", "architecture", "generated_files", "validations", "judge_report", "artifacts"):
        if key not in payload:
            failures.append(f"{label} missing {key}")
    if not any(item.get("success") for item in payload.get("validations", [])):
        failures.append(f"{label} must include at least one successful validation")
    if payload.get("judge_report", {}).get("pass_status") is not True:
        failures.append(f"{label} judge_report pass_status must be true")
    return failures


def _check_forbidden_content() -> list[str]:
    failures: list[str] = []
    skipped_dirs = {"__pycache__", ".git", ".venv", "venv", "dist"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in skipped_dirs for part in path.parts):
            continue
        if path.suffix.lower() in {".pyc", ".png", ".jpg", ".jpeg", ".mp4"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                rel = path.relative_to(ROOT).as_posix()
                failures.append(f"forbidden pattern {pattern!r} in {rel}")
    return failures


def _run_command(command: list[str], cwd: Path = ROOT) -> list[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.returncode == 0:
        return []
    return [
        "command failed: " + " ".join(command) + f" (cwd={cwd.relative_to(ROOT).as_posix() if cwd != ROOT else '.'})",
        result.stdout.strip(),
        result.stderr.strip(),
    ]


if __name__ == "__main__":
    raise SystemExit(main())
