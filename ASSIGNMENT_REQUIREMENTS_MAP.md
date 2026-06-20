# HW7 Assignment Requirements Map

This document maps the current project artifacts to the HW7 submission
requirements and highlights the remaining gaps before final handoff.

## Requirement Coverage

| HW7 requirement | Current project alignment | Evidence in repo |
| --- | --- | --- |
| LLM / agent workflow | The primary `api` mode calls an OpenAI-compatible model for the Mini-Codex Patch Agent. `mock_test` is kept for deterministic tests and offline verification. | `app.py`, `assignment_core/workbench.py`, `assignment_core/model_client.py`, `AI_USAGE.md` |
| Optional live API test | The project can call an OpenAI-compatible chat completion provider for real model-backed patch proposals when credentials are configured through environment variables or the UI password field. | `assignment_core/model_client.py`, `API_TESTING.md`, `outputs/workbench_live/`, `demo_materials/screenshots/` |
| Code generation / modification | The Patch Agent can create or modify concrete files inside the selected workspace, including Python projects, static web apps, tests, and documentation. | `assignment_core/workbench.py`, `workspace/`, `outputs/workbench_latest/proposal.json`, `outputs/workbench_latest/apply_result.json` |
| README | The README explains the project purpose, scope, UI/CLI run commands, generated artifacts, and architecture flow. | `README.md` |
| AI usage explanation | The package explains where AI is used, what remains human-controlled, how mock/live modes differ, and which evidence proves the run. | `AI_USAGE.md`, `WORKFLOW_LOG.md`, `README.md` |
| Workflow log | The workflow log records the Mini-Codex flow: user request, context loading, patch proposal, diff review, human apply, validation, repair, and preview. | `WORKFLOW_LOG.md` |
| Dependency list | The dependency file lists Streamlit and Pydantic for the dashboard and structured schemas. | `requirements.txt` |
| Demo materials | Screenshots and demo notes are available for classroom demonstration of the Mini-Codex chat flow and Live API patch generation. | `demo_materials/screenshots/`, `DEMO_SCRIPT.md`, `outputs/workbench_latest/` |
| Source repo | The standalone source workspace contains the runner, assignment core package, tests, docs, example input, dependency list, and generated demo output. | `run_council.py`, `assignment_core/`, `tests/`, `README.md`, `WORKFLOW_LOG.md`, `requirements.txt` |
| Submission preparation | The project includes a final verifier, clean packaging script, TXT generator, and course submission template so final packaging can be completed once the student ID and public link are known. | `final_check.py`, `create_submission_package.py`, `create_submission_txt.py`, `SUBMISSION_TEMPLATE.md`, `QA_CHECKLIST.md` |

## Remaining Gap Checklist

- [x] Decide whether the final interface will use Streamlit, Gradio, or a
  lightweight command-line demo only.
- [x] Add final demo screenshots or a short demo video from the Streamlit interface.
- [x] Re-run the test suite and demo command immediately before submission.
- [x] Add a final local verifier for required files and core output contract.
- [x] Add a clean zip packaging path excluding caches/logs/local-only files.
- [x] Add a required TXT generator for the final student-id-based submission file.
- [x] Confirm whether the final recorded demo uses `api` mode or clearly labels
  `mock_test` as an offline fallback.
