# Project Status

Date: 2026-06-20

## Current Primary Design

Mini-Codex code modification workbench.

The assignment package now focuses on an interactive coding-agent workflow:

```text
workspace context
  -> chat request
  -> patch proposal
  -> diff review
  -> human apply
  -> validation
  -> repair or preview
```

The earlier agentic experiment orchestrator is retained as auxiliary evidence,
but the main submitted experience is the Mini-Codex workbench in `app.py` and
`assignment_core/workbench.py`.

## Current Completion

Mini-Codex workbench:

- Status: implemented and locally verifiable.
- Completion: about 90%.

Full assignment submission:

- Status: package can be verified locally; Live API workbench evidence, demo
  media, and public submission link are still pending.
- Completion: about 90%.

## Done

- Streamlit Mini-Codex UI with three working zones:
  - workspace and conversation list
  - central chat timeline and visible `Message Mini-Codex` composer
  - inspector for validation, repair, undo, and preview
- `assignment_core/workbench.py` implements:
  - context loading
  - hash-aware patch proposal
  - mock patch mode
  - OpenAI-compatible Live API patch mode
  - diff rendering
  - human-gated apply
  - validation
  - restore / Undo Apply
  - preview launcher for Streamlit `app.py` or static `index.html`
  - workspace zip export
- Workspaces stay inside the HW package `workspace/` directory, but their
  contents are not locked to a single template.
- `Empty workspace` starts as an empty local folder; the agent can create new
  files from the user request.
- Optional demo templates remain available only as shortcuts:
  - `Demo Streamlit starter`
  - `Minimal Python starter`
- Mock code patch flow works.
- Proposal diffs are shown before writing.
- Apply writes concrete files under the currently selected workspace.
- Validation runs after apply.
- Preview launcher is available after validation passes when the workspace has
  a supported preview entry.
- Evidence files are generated under `outputs/workbench_latest/`.
- Chat transcript is saved as Markdown and JSON.
- Download buttons expose proposal, apply result, restore result, transcript,
  workflow log, and current workspace zip.
- Unit tests cover workbench behavior and UI helper logic.
- Submission zip is generated at:

```text
dist/hw7-agentic-experiment-orchestrator.zip
```

## Pending

- Live API Mini-Codex patch run saved under:

```text
outputs/workbench_live/
```

  Current status: completed with DeepSeek after stripping surrounding quotes
  from the local `.env` value before setting the process environment variable.

- Demo video or screenshots showing:
  - entering a request in `Message Mini-Codex`
  - reviewing the generated diff
  - applying the patch
  - validation passing
  - preview launch
  - evidence downloads
- GitHub repository or shared link.
- Final student ID specific submission text.

## Auxiliary Evidence

The older Planner / Architect / Coder / Judge project-generator flow remains in:

```text
outputs/demo_run/
outputs/live_api_run/
run_council.py
assignment_core/agents.py
assignment_core/runner.py
```

It is useful supporting evidence, but it should not be presented as the primary
project anymore.

## Current Blockers

- Student ID is needed before creating the final `<StudentID>_HW7.txt`.
- Public repository or shared-drive destination is needed before final
  submission packaging.
- A screenshot or short demo video still needs to be captured from the
  Streamlit UI.
