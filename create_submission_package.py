from __future__ import annotations

import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PACKAGE_DIR = ROOT / "dist"
PACKAGE_PATH = PACKAGE_DIR / "hw7-agentic-experiment-orchestrator.zip"

INCLUDE_PATHS = [
    ".gitignore",
    "README.md",
    "AI_USAGE.md",
    "WORKFLOW_LOG.md",
    "AGENT_ASSIGNMENT.md",
    "ASSIGNMENT_REQUIREMENTS_MAP.md",
    "PROJECT_STATUS.md",
    "QA_CHECKLIST.md",
    "DEMO_SCRIPT.md",
    "API_TESTING.md",
    "SUBMISSION_TEMPLATE.md",
    ".streamlit",
    "requirements.txt",
    "app.py",
    "start_demo.py",
    "run_council.py",
    "final_check.py",
    "create_submission_txt.py",
    "create_submission_package.py",
    "scripts",
    "demo_materials",
    "examples",
    "workspace",
    "assignment_core",
    "tests",
    "outputs/workbench_latest",
    "outputs/workbench_live",
    "outputs/demo_run",
    "outputs/live_api_run",
    "outputs/ui_latest",
]

EXCLUDED_DIR_NAMES = {"__pycache__", ".pytest_cache", ".venv", "venv", ".git"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log"}


def main() -> int:
    PACKAGE_DIR.mkdir(exist_ok=True)
    if PACKAGE_PATH.exists():
        PACKAGE_PATH.unlink()

    included_files = _collect_files()
    with zipfile.ZipFile(PACKAGE_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in included_files:
            archive.write(path, path.relative_to(ROOT).as_posix())

    print(f"wrote {PACKAGE_PATH}")
    print(f"files {len(included_files)}")
    return 0


def _collect_files() -> list[Path]:
    files: list[Path] = []
    for rel in INCLUDE_PATHS:
        path = ROOT / rel
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(_iter_included_dir(path))
        else:
            raise FileNotFoundError(f"required package path missing: {rel}")
    return sorted(set(files), key=lambda item: item.relative_to(ROOT).as_posix())


def _iter_included_dir(path: Path) -> list[Path]:
    files: list[Path] = []
    for candidate in path.rglob("*"):
        if not candidate.is_file():
            continue
        if any(part in EXCLUDED_DIR_NAMES for part in candidate.relative_to(ROOT).parts):
            continue
        if candidate.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        files.append(candidate)
    return files


if __name__ == "__main__":
    raise SystemExit(main())
