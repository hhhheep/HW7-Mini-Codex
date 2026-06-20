# Mini-Codex: Agentic Code Modification Workbench

## Overview

Mini-Codex is a small agentic coding assistant for local workspaces inside this HW package. The user selects or creates a workspace, chats with a coding agent about a desired change, reviews the agent-proposed file replacements and diffs inside the conversation, approves the change, then the system writes real files, runs local validation, and can launch a preview when the workspace has a supported entry point.

The workspace path is restricted to the package-owned `workspace/` directory for safety and reproducibility, but the workspace contents are not locked to one template. An empty workspace can start with no files, and the agent can create new files such as `main.py`, `index.html`, helper modules, tests, and documentation.

The main interaction is:

```text
natural language request
  -> context loader reads current files and hashes
  -> code agent proposes full-file replacements
  -> chat UI shows summary and unified diffs
  -> user applies or rejects
  -> patch applier verifies old hashes and writes files
  -> validator runs compileall and unittest
  -> workflow log preserves evidence
```

The included `run_council.py` project-generation workflow is kept as auxiliary evidence from the earlier assignment package. The primary UI and demo direction is now the Mini-Codex code modification loop.

## Architecture

```text
Streamlit UI
  -> User Change Request
  -> Context Loader
  -> Patch Planner / Code Patch Agent
  -> Diff Renderer
  -> Human Approval
  -> Safe Patch Applier
  -> Local Validator
  -> Preview Launcher
  -> Workflow Logger / Evidence Export
```

## Key Modules

- `app.py`: Streamlit Mini-Codex chat interface with workspace/conversation list, chat timeline, diff review, apply/reject/revise actions, validation, preview, and evidence panels.
- `assignment_core/workbench.py`: context loading, file hashing, mock/API patch proposal, safe apply, local validation, preview launch, and workflow log writing.
- `assignment_core/model_client.py`: OpenAI-compatible live API client.
- `workspace/generated_project/`: editable sample workspace used in the deterministic demo evidence.
- `workspace/*/`: additional local workspaces created or selected through the UI.
- `tests/test_workbench.py`: tests the mock code-change flow, hash mismatch protection, and context hashing.
- `assignment_core/runner.py` and `assignment_core/agents.py`: retained project-generation workflow used for supporting mock/live evidence.

## Demo Flow

1. Start the Streamlit UI.
2. Create a new `Empty workspace`, or inspect `workspace/generated_project/`.
3. Enter a change request such as:

```text
Create a Python CLI project with main.py, README.md, and offline unittest tests.
```

4. Click `Run Agent`.
5. Review the assistant summary and diffs in the chat timeline.
6. Click `Apply`.
7. Confirm compile and unittest validation pass.
8. Launch the preview on port `8502` when the workspace has `app.py` or `index.html`.
9. Open the Evidence tab to download `WORKFLOW_LOG.md`, `proposal.json`, and `apply_result.json`.

## Modes

### Mock Test

`mock_test` mode is deterministic and offline. It supports the assignment demo requests for generation history, CSV export, and classroom-friendly UI. This mode is used for stable unit tests.

### Live API

`Live API` mode calls an OpenAI-compatible backend for the patch proposal. It uses environment-driven configuration and does not write API keys into artifacts.

Supported environment variables:

```powershell
$env:HW7_LLM_API_KEY = "<YOUR_API_KEY>"
$env:HW7_LLM_BASE_URL = "https://api.openai.com/v1"
$env:HW7_DISCUSSION_MODEL = "gpt-4o-mini"
$env:HW7_WRITER_MODEL = "gpt-4o-mini"
```

The Streamlit UI also provides per-run API fields. The password input is used only in memory for that run.

## Local Run

```powershell
cd <project-root>
python -m pip install -r requirements.txt
streamlit run app.py
```

On Windows, a detached local launcher is available:

```powershell
python start_demo.py
```

Run tests:

```powershell
python -m unittest discover -s tests
```

Run final verification:

```powershell
python final_check.py
```

Build the submission zip:

```powershell
python create_submission_package.py
```

The zip is written to:

```text
dist/hw7-agentic-experiment-orchestrator.zip
```

## Evidence Included

- `outputs/workbench_latest/`: Mini-Codex mock code-modification run with proposal, diff, apply result, validation logs, and workflow log.
- `outputs/demo_run/`: deterministic project-generation evidence retained from the earlier package.
- `outputs/live_api_run/`: live API project-generation evidence with prompts, raw model responses, validation, and judge result.
- `outputs/ui_latest/`: live API run produced through the Streamlit UI before the Mini-Codex refactor.

## Submission Notes

The package excludes provider credentials, virtual environments, caches, and unrelated local files. Remaining manual items are student ID, public repository/share link, and demo screenshot or video.
