from __future__ import annotations

import json
from typing import TypeVar

from pydantic import BaseModel, TypeAdapter, ValidationError

from .model_client import ModelConfig, chat_completion
from .schemas import AgentOutput, ArchitectureSpec, GeneratedFile, JudgeReport, PlanStep, TaskSpec, ValidationResult


T = TypeVar("T", bound=BaseModel)


def planner_mock(project_idea: str) -> tuple[TaskSpec, AgentOutput]:
    spec = TaskSpec(
        title="Generated AI Experiment App",
        objective=f"Build and validate a small generative-AI application from this task: {project_idea.strip()}",
        constraints=[
            "single-machine demo",
            "no remote SSH/GPU orchestration",
            "generated files must be locally validated",
            "workflow log must preserve prompts, outputs, and validation results",
        ],
        target_stack=["Python", "Streamlit", "OpenAI-compatible LLM API optional"],
        success_criteria=[
            "generated_project contains runnable starter files",
            "generated files pass compile validation",
            "tests pass with an allowlisted command",
            "final report explains artifacts and remaining gaps",
        ],
    )
    output = AgentOutput(
        role="Planner Agent",
        summary="Converted the user request into a bounded experiment task specification.",
        decisions=[
            "Use a local single-machine generated project.",
            "Validate generated code with allowlisted commands.",
            "Keep external model calls configurable through environment variables.",
        ],
        artifacts_to_create=["TaskSpec JSON", "milestone plan"],
        next_steps=["Architect Agent designs the generated project structure."],
    )
    return spec, output


def architect_mock(task_spec: TaskSpec) -> tuple[ArchitectureSpec, AgentOutput]:
    plan = [
        PlanStep(
            id="P1",
            goal="Create generated app scaffold",
            inputs=["TaskSpec"],
            outputs=["generated_project/app.py", "generated_project/requirements.txt"],
            risk="Generated UI may be too generic if the task is underspecified.",
        ),
        PlanStep(
            id="P2",
            goal="Add documentation and tests",
            inputs=["TaskSpec", "generated app scaffold"],
            outputs=["generated_project/README.md", "generated_project/tests/test_basic.py"],
            risk="Tests must avoid requiring unavailable API keys.",
        ),
        PlanStep(
            id="P3",
            goal="Validate and report",
            inputs=["generated_project"],
            outputs=["validation results", "final_report.md", "WORKFLOW_LOG.md"],
            risk="Validation should stay allowlisted and not execute arbitrary generated behavior.",
        ),
    ]
    architecture = ArchitectureSpec(
        summary="Single-machine generated-project pipeline with local validation and report collection.",
        modules=[
            "Streamlit generated app",
            "Generated project tests",
            "Allowlisted runner",
            "Artifact collector",
            "Judge/reporter",
        ],
        data_flow=[
            "TaskSpec -> ArchitectureSpec",
            "ArchitectureSpec -> GeneratedFile list",
            "GeneratedFile list -> generated_project/",
            "generated_project/ -> validation commands",
            "validation results -> JudgeReport and final report",
        ],
        file_structure=[
            "generated_project/app.py",
            "generated_project/requirements.txt",
            "generated_project/README.md",
            "generated_project/tests/test_basic.py",
        ],
        plan=plan,
    )
    output = AgentOutput(
        role="Architect Agent",
        summary="Designed a generated-project structure and validation flow.",
        decisions=[
            "Generate actual runnable starter files.",
            "Run compileall and unittest discovery as safe validation commands.",
            "Package generated_project as a downloadable zip.",
        ],
        artifacts_to_create=architecture.file_structure,
        next_steps=["Coder Agent writes generated_project files."],
    )
    return architecture, output


def coder_mock(task_spec: TaskSpec, architecture: ArchitectureSpec) -> tuple[list[GeneratedFile], AgentOutput]:
    app_py = f'''from __future__ import annotations

import streamlit as st


st.set_page_config(page_title="{_escape(task_spec.title)}", layout="wide")
st.title("{_escape(task_spec.title)}")
st.write("{_escape(task_spec.objective)}")

prompt = st.text_area("Experiment prompt", "Compare two prompt variants for a generative AI demo.")
seed = st.number_input("Seed", value=42, step=1)

if st.button("Create experiment record"):
    st.subheader("Generated experiment record")
    st.json({{
        "prompt": prompt,
        "seed": int(seed),
        "status": "recorded",
        "note": "Replace this stub with a real LLM or diffusion backend when credentials/GPU are available.",
    }})
'''
    requirements = "streamlit>=1.35\n"
    readme = f"""# {task_spec.title}

## Objective

{task_spec.objective}

## Run

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

## Validation

This generated project is validated by the parent orchestrator with:

```powershell
python -m compileall generated_project
python -m unittest discover -s generated_project/tests
```
"""
    test_basic = '''from __future__ import annotations

import unittest
from pathlib import Path


class GeneratedProjectTest(unittest.TestCase):
    def test_required_files_exist(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.assertTrue((root / "app.py").exists())
        self.assertTrue((root / "requirements.txt").exists())
        self.assertTrue((root / "README.md").exists())


if __name__ == "__main__":
    unittest.main()
'''
    files = [
        GeneratedFile(path="app.py", content=app_py, purpose="Streamlit generated experiment app"),
        GeneratedFile(path="requirements.txt", content=requirements, purpose="Generated project dependencies"),
        GeneratedFile(path="README.md", content=readme, purpose="Generated project documentation"),
        GeneratedFile(path="tests/test_basic.py", content=test_basic, purpose="Basic generated project validation test"),
    ]
    output = AgentOutput(
        role="Coder Agent",
        summary="Generated actual starter project files under generated_project/.",
        decisions=[
            "Use a Streamlit app stub that records experiment parameters.",
            "Keep generated code runnable without API keys.",
            "Include unittest-based file existence validation.",
        ],
        artifacts_to_create=[item.path for item in files],
        next_steps=["Runner validates generated files with allowlisted commands."],
    )
    return files, output


def judge_mock(
    task_spec: TaskSpec,
    generated_files: list[GeneratedFile],
    validations: list[ValidationResult],
) -> JudgeReport:
    missing = []
    expected = {"app.py", "requirements.txt", "README.md", "tests/test_basic.py"}
    found = {item.path for item in generated_files}
    for path in sorted(expected - found):
        missing.append(f"missing generated file: {path}")
    for result in validations:
        if not result.success:
            missing.append(f"validation failed: {result.command}")
    return JudgeReport(
        pass_status=not missing,
        missing_requirements=missing,
        suggested_fixes=[] if not missing else ["Regenerate files or inspect validation stderr."],
        final_summary=(
            "Generated project satisfies the minimum HW7 agentic workflow validation."
            if not missing
            else "Generated project has gaps that must be repaired before submission."
        ),
    )


def planner_api(project_idea: str, config: ModelConfig) -> tuple[TaskSpec, AgentOutput]:
    prompt = """Return JSON matching this schema:
{"title": str, "objective": str, "constraints": [str], "target_stack": [str], "success_criteria": [str]}

Task: convert the user request into a bounded generative-AI experiment TaskSpec.
Do not include credentials, private paths, SSH, or remote GPU requirements."""
    spec, raw = _call_structured(config, config.discussion_model, "Planner Agent", prompt, project_idea, TaskSpec)
    output = AgentOutput(
        role="Planner Agent",
        summary="Created TaskSpec from user request using live model output.",
        decisions=spec.success_criteria,
        artifacts_to_create=["TaskSpec JSON"],
        next_steps=["Architect Agent consumes TaskSpec."],
        prompt=prompt,
        raw_response=raw,
    )
    return spec, output


def architect_api(task_spec: TaskSpec, config: ModelConfig) -> tuple[ArchitectureSpec, AgentOutput]:
    prompt = """Return JSON matching this schema:
{
 "summary": str,
 "modules": [str],
 "data_flow": [str],
 "file_structure": [str],
 "plan": [{"id": str, "goal": str, "inputs": [str], "outputs": [str], "risk": str}]
}

Design a single-machine generated project and validation flow for the TaskSpec.
The generated project contract is intentionally small for this assignment:
exactly app.py, requirements.txt, README.md, and tests/test_basic.py.
Do not require extra Python modules, a git repository, workflow_log.md inside
the generated project, cloud services, GPUs, or network access for tests."""
    architecture, raw = _call_structured(
        config,
        config.discussion_model,
        "Architect Agent",
        prompt,
        task_spec.model_dump_json(indent=2),
        ArchitectureSpec,
    )
    architecture = _normalize_architecture_contract(architecture)
    output = AgentOutput(
        role="Architect Agent",
        summary=architecture.summary,
        decisions=architecture.modules,
        artifacts_to_create=architecture.file_structure,
        next_steps=["Coder Agent creates the listed files."],
        prompt=prompt,
        raw_response=raw,
    )
    return architecture, output


def coder_api(task_spec: TaskSpec, architecture: ArchitectureSpec, config: ModelConfig) -> tuple[list[GeneratedFile], AgentOutput]:
    prompt = """Return JSON as a list of files:
[{"path": str, "content": str, "purpose": str}]

Generate actual project files under generated_project. Required relative paths:
app.py, requirements.txt, README.md, tests/test_basic.py.
The generated project must be self-contained in exactly those files.
Do not import helper modules such as api_client.py, mock_responses.py, prompt_comparator.py,
or any file that is not included in the JSON list.
All app logic, deterministic fallback logic, and optional API-call stubs must live in app.py.
The generated tests must use unittest, must not require network access or API keys,
and must pass with: python -m unittest discover -s generated_project/tests.
Tests may check file existence, source text, and pure helper functions, but must not
click Streamlit controls or expect a real Streamlit runtime."""
    adapter: TypeAdapter[list[GeneratedFile]] = TypeAdapter(list[GeneratedFile])
    files, raw = _call_structured_adapter(
        config,
        config.writer_model,
        "Coder Agent",
        prompt,
        json.dumps(
            {"task_spec": task_spec.model_dump(), "architecture": architecture.model_dump()},
            ensure_ascii=False,
            indent=2,
        ),
        adapter,
    )
    output = AgentOutput(
        role="Coder Agent",
        summary="Generated actual project files using live model output.",
        decisions=["Write generated_project files", "Keep validation local and allowlisted"],
        artifacts_to_create=[item.path for item in files],
        next_steps=["Runner writes and validates generated files."],
        prompt=prompt,
        raw_response=raw,
    )
    return files, output


def coder_repair_api(
    task_spec: TaskSpec,
    architecture: ArchitectureSpec,
    generated_files: list[GeneratedFile],
    validations: list[ValidationResult],
    config: ModelConfig,
) -> tuple[list[GeneratedFile], AgentOutput]:
    prompt = """Return JSON as a full replacement list of files:
[{"path": str, "content": str, "purpose": str}]

The previous generated project failed local validation. Repair it.
Keep exactly these relative paths: app.py, requirements.txt, README.md, tests/test_basic.py.
Do not add helper files. Do not require network access or API keys in tests.
Make the tests and implementation consistent with each other.
The repaired project must pass:
python -m compileall generated_project
python -m unittest discover -s generated_project/tests."""
    adapter: TypeAdapter[list[GeneratedFile]] = TypeAdapter(list[GeneratedFile])
    files, raw = _call_structured_adapter(
        config,
        config.writer_model,
        "Coder Repair Agent",
        prompt,
        json.dumps(
            {
                "task_spec": task_spec.model_dump(),
                "architecture": architecture.model_dump(),
                "generated_files": [item.model_dump() for item in generated_files],
                "validation_results": [item.model_dump() for item in validations],
            },
            ensure_ascii=False,
            indent=2,
        ),
        adapter,
    )
    output = AgentOutput(
        role="Coder Repair Agent",
        summary="Revised the generated project after validation feedback from the runner.",
        decisions=[
            "Use validation stderr/stdout as repair input.",
            "Return a full replacement for the same four-file generated project contract.",
        ],
        artifacts_to_create=[item.path for item in files],
        next_steps=["Runner rewrites generated_project and validates again."],
        prompt=prompt,
        raw_response=raw,
    )
    return files, output


def judge_api(
    task_spec: TaskSpec,
    architecture: ArchitectureSpec,
    generated_files: list[GeneratedFile],
    validations: list[ValidationResult],
    config: ModelConfig,
) -> JudgeReport:
    prompt = """Return JSON matching this schema:
{"pass_status": bool, "missing_requirements": [str], "suggested_fixes": [str], "final_summary": str}

Judge only this generated-project contract:
1. Required files exist: app.py, requirements.txt, README.md, tests/test_basic.py.
2. The generated app addresses the TaskSpec as a small generative-AI experiment app.
3. Tests are offline and do not require API keys or network access.
4. All provided validation results pass.

Do not require a git repository, extra modules, GPU/cloud services, or workflow_log.md
inside the generated project. The parent orchestrator writes WORKFLOW_LOG.md and final_report.md."""
    report, raw = _call_structured(
        config,
        config.discussion_model,
        "Judge Agent",
        prompt,
        json.dumps(
            {
                "task_spec": task_spec.model_dump(),
                "architecture": architecture.model_dump(),
                "generated_files": [item.model_dump() for item in generated_files],
                "validations": [item.model_dump() for item in validations],
            },
            ensure_ascii=False,
            indent=2,
        ),
        JudgeReport,
    )
    return report.model_copy(update={"prompt": prompt, "raw_response": raw})


def _normalize_architecture_contract(architecture: ArchitectureSpec) -> ArchitectureSpec:
    expected_files = [
        "generated_project/app.py",
        "generated_project/requirements.txt",
        "generated_project/README.md",
        "generated_project/tests/test_basic.py",
    ]
    expected_modules = [
        "Generated Streamlit app in app.py",
        "Generated README",
        "Generated unittest tests",
        "Parent runner validation and reporting",
    ]
    data_flow = [
        "TaskSpec -> four-file generated project contract",
        "Generated files -> generated_project/",
        "generated_project/ -> compileall and unittest validation",
        "validation results -> JudgeReport and parent workflow report",
    ]
    plan = [
        PlanStep(
            id="P1",
            goal="Generate app.py with UI, deterministic fallback behavior, and optional API configuration hooks.",
            inputs=["TaskSpec"],
            outputs=["generated_project/app.py"],
            risk="Generated code must stay runnable without secrets.",
        ),
        PlanStep(
            id="P2",
            goal="Generate dependency and usage documentation.",
            inputs=["TaskSpec", "app.py"],
            outputs=["generated_project/requirements.txt", "generated_project/README.md"],
            risk="Documentation must not contain private API keys.",
        ),
        PlanStep(
            id="P3",
            goal="Generate offline unittest coverage for stable helper behavior and required files.",
            inputs=["app.py"],
            outputs=["generated_project/tests/test_basic.py"],
            risk="Tests must not depend on Streamlit runtime interaction, network access, or API keys.",
        ),
    ]
    return architecture.model_copy(
        update={
            "modules": expected_modules,
            "data_flow": data_flow,
            "file_structure": expected_files,
            "plan": plan,
        }
    )


def _call_structured(
    config: ModelConfig,
    model: str,
    role: str,
    system_prompt: str,
    user_payload: str,
    schema: type[T],
) -> tuple[T, str]:
    raw = chat_completion(config, model, system_prompt, user_payload)
    try:
        return schema.model_validate_json(_extract_json(raw)), raw
    except ValidationError as exc:
        repair_prompt = (
            f"Your previous {role} response failed schema validation. "
            f"Return only valid JSON for the requested schema. Error: {exc}"
        )
        repaired = chat_completion(config, model, repair_prompt, raw)
        return schema.model_validate_json(_extract_json(repaired)), repaired


def _call_structured_adapter(
    config: ModelConfig,
    model: str,
    role: str,
    system_prompt: str,
    user_payload: str,
    adapter: TypeAdapter,
):
    raw = chat_completion(config, model, system_prompt, user_payload)
    try:
        return adapter.validate_json(_extract_json(raw)), raw
    except ValidationError as exc:
        repair_prompt = (
            f"Your previous {role} response failed schema validation. "
            f"Return only valid JSON for the requested schema. Error: {exc}"
        )
        repaired = chat_completion(config, model, repair_prompt, raw)
        return adapter.validate_json(_extract_json(repaired)), repaired


def _extract_json(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    start_candidates = [idx for idx in (stripped.find("{"), stripped.find("[")) if idx >= 0]
    if not start_candidates:
        return stripped
    start = min(start_candidates)
    end = max(stripped.rfind("}"), stripped.rfind("]"))
    return stripped[start : end + 1]


def _escape(text: str) -> str:
    return " ".join(text.replace('"', "'").split())
