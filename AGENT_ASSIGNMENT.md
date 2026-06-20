# Agent Assignment Plan

This folder contains the HW7-sized version of an agentic generative-AI experiment
orchestrator. It keeps the real task flow, but removes remote workers, SSH,
long-running queues, and private research infrastructure.

## Active Agents

### Planner Agent

Owns:

- Reading the user experiment/app idea.
- Producing a structured `TaskSpec`.
- Defining constraints, target stack, and success criteria.

Output:

- `TaskSpec` JSON.

### Architect Agent

Owns:

- Designing the generated project structure.
- Defining data flow and implementation plan.
- Selecting local validation boundaries.

Output:

- `ArchitectureSpec` JSON with plan steps.

### Coder Agent

Owns:

- Generating actual starter project files.
- Consuming Planner and Architect outputs.
- Writing at least `app.py`, `requirements.txt`, `README.md`, and `tests/test_basic.py`.

Output:

- `GeneratedFile[]` written under `generated_project/`.

### Runner and Collector

Owns:

- Running allowlisted local validation commands.
- Capturing stdout, stderr, return status, and generated artifact metadata.
- Avoiding arbitrary execution of generated code.

Output:

- `ValidationResult[]`.

### Judge Agent

Owns:

- Checking generated files and validation results against the HW7 rubric.
- Identifying missing requirements and suggested fixes.

Output:

- `JudgeReport` JSON.

### Reporter

Owns:

- Writing the auditable workflow log.
- Writing the final report.
- Packaging the generated project zip.

Output:

- `WORKFLOW_LOG.md`
- `final_report.md`
- `generated_project.zip`

## Automation Contract

Run:

```powershell
python run_council.py --mode mock_test --idea-file examples\project_idea.txt --output outputs\demo_run
```

Required outputs:

- `run.json`
- `generated_project/`
- `generated_project.zip`
- `WORKFLOW_LOG.md`
- `final_report.md`

## Next Work Queue

1. Run a real `--mode api` smoke test after a provider key is configured.
2. Record demo screenshot/video from the Streamlit dashboard.
3. Prepare public repository/share link and final `<StudentID>_HW7.txt`.
