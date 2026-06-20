# Mini-Codex Agent Workflow Log

Project title: Mini-Codex Code Modification Workbench

## Current Primary Workflow

The submitted system is now centered on a Mini-Codex style agentic code
modification loop. The user selects a workspace, sends a natural-language code
change request, reviews the proposed patch, applies it only after human
approval, validates the result, repairs if needed, and launches a local preview.

```text
User request
  -> Context Loader
  -> Patch Agent
  -> Diff Review
  -> Human Apply
  -> Validator
  -> Repair if needed
  -> Preview
```

This is the main assignment story: an LLM-backed coding agent proposes concrete
file edits, preserves the evidence, and keeps the human in control of the write
step.

## Agent Roles

### User Request

Input:

- A natural-language change request from the central `Message Mini-Codex`
  composer.

Example:

```text
Add a CSV export button for the generation history.
```

Output:

- A bounded patch task attached to the active conversation and workspace.

### Context Loader

Implemented in `assignment_core/workbench.py`.

Input:

- The currently selected local workspace under the package-owned `workspace/`
  directory.

Workspace policy:

- The path is restricted to the HW package for safety and reproducibility.
- The workspace contents are not locked to one template.
- An empty workspace may start with no files; the patch agent can create new
  files when the user requests a new project.
- Demo starters are optional shortcuts, not the core capability.

Output:

- Selected editable files.
- SHA-256 file hashes.
- Rejected file metadata for unsupported or generated files.
- A compact project summary for the patch agent.

Purpose:

- Give the agent real code context.
- Prevent stale patches from being applied after the workspace changes.

### Patch Agent

Implemented through `propose_changes()` in `assignment_core/workbench.py`.

Modes:

- `mock_test`: deterministic offline patch generation for repeatable tests.
- `api`: OpenAI-compatible model-backed patch generation.

Output:

- `outputs/workbench_latest/proposal.json`
- `kind: mini_codex_proposal`
- proposal metadata: mode, provider, created time
- context snapshot
- changed files with `old_content_hash`
- expected visible behavior
- unified diffs
- prompt/raw model response when Live API is used

### Diff Review

Implemented in `app.py`.

UI evidence:

- Chat transcript.
- Request / Proposal / Validation / Preview timeline.
- Proposal run table showing Mock vs Live API and model names.
- Proposal impact table showing changed file, reason, and context status.
- Diff expanders for every changed file.
- Next action guidance.

Purpose:

- The system does not silently write files.
- The human can inspect, revise, reject, or apply the patch.

### Human Apply

Implemented through `apply_changeset()` in `assignment_core/workbench.py`.

Behavior:

- Applies only files whose `old_content_hash` still matches the current
  workspace.
- Writes a snapshot under `outputs/workbench_latest/snapshots/`.
- Produces `outputs/workbench_latest/apply_result.json`.
- Appends apply evidence to `outputs/workbench_latest/WORKFLOW_LOG.md`.

The UI also supports `Undo Apply`, implemented through
`restore_changeset_snapshot()`, which restores the previous snapshot and writes
`restore_result.json`.

### Validator

Implemented through `validate_workspace()` in `assignment_core/workbench.py`.

Allowlisted validation commands:

```powershell
python -m compileall workspace/generated_project
python -m unittest discover -s tests
```

The stored command text is sanitized and does not include local absolute Python
paths.

Output:

- validation command
- success flag
- stdout
- stderr

### Repair If Needed

If validation fails, the Inspector exposes `Repair with Agent`.

Behavior:

- The failed validation logs are folded into a repair request.
- The patch agent generates a new proposal.
- The human still reviews the diff before applying.

### Preview

After validation passes, the Inspector exposes `Launch Preview on 8502`.

Preview entries:

- `app.py` launches with Streamlit.
- `index.html` launches with a local static HTTP server.
- Other project types can still be generated and validated; they simply may not
  have a one-click preview until a supported preview entry exists.

Output:

- local preview URL
- preview process id
- downloadable current workspace zip

## Primary Evidence Files

The Mini-Codex workbench evidence is stored under:

```text
outputs/workbench_latest/
```

Expected files:

```text
outputs/workbench_latest/proposal.json
outputs/workbench_latest/apply_result.json
outputs/workbench_latest/WORKFLOW_LOG.md
outputs/workbench_latest/CHAT_TRANSCRIPT.md
outputs/workbench_latest/chat_transcript.json
outputs/workbench_latest/current_workspace.zip
```

Live API evidence should be stored under:

```text
outputs/workbench_live/
```

Expected Live API story:

```text
Mock mode proves deterministic offline validation.
Live API mode proves the LLM-backed code patch workflow.
```

## Auxiliary Evidence

The earlier Planner / Architect / Coder / Judge project generator is retained as
auxiliary evidence only. It demonstrates a second agentic workflow and preserves
historical work, but it no longer defines the primary project direction.

Auxiliary outputs:

```text
outputs/demo_run/
outputs/live_api_run/
```

Old auxiliary flow:

```text
TaskSpec input
  -> Planner Agent
  -> Architect Agent
  -> Coder Agent
  -> Runner / Collector
  -> Judge Agent
  -> Reporter
```

## Verification Commands

Run from the project root:

```powershell
python -m unittest discover -s tests
python final_check.py
python create_submission_package.py
```

To demonstrate the Mini-Codex UI:

```powershell
python start_demo.py
```

Then open:

```text
http://localhost:8501/
```

## Remaining Manual Items

- Preserve the completed Live API Mini-Codex patch evidence under
  `outputs/workbench_live/`.
- Record a short demo video or screenshot sequence.
- Provide the student ID.
- Provide a public repository or share link.
