# HW7 Assignment Requirements Map

This document maps the current project artifacts to the HW7 submission
requirements and highlights the remaining gaps before final handoff.

## Requirement Coverage

| HW7 requirement | Current project alignment | Evidence in repo |
| --- | --- | --- |
| LLM / agent workflow | The normal `api` mode calls OpenAI-compatible models for Planner, Architect, Coder, and Judge. `mock_test` is kept only for unit tests and offline verification. | `assignment_core/agents.py`, `assignment_core/model_client.py`, `run_council.py --mode api` |
| Optional live API test | The project can call an OpenAI-compatible chat completion provider for real model-backed discussion and writer outputs when credentials are configured via environment variables. | `assignment_core/model_client.py`, `API_TESTING.md`, `run_council.py --mode api` |
| Code generation | The Coder Agent generates actual files under `generated_project/`, including app code, requirements, README, and tests. | `assignment_core/agents.py`, `outputs/demo_run/generated_project/`, `outputs/demo_run/generated_project.zip` |
| README | The README explains the project purpose, scope, UI/CLI run commands, generated artifacts, and architecture flow. | `README.md` |
| Workflow log | The workflow log records project selection, agent-assisted planning, architecture reduction, implementation steps, bottlenecks, and verification commands. | `WORKFLOW_LOG.md` |
| Dependency list | The dependency file lists Streamlit and Pydantic for the dashboard and structured schemas. | `requirements.txt` |
| Demo materials | A sample project idea, generated demo outputs, recording script, and demo-materials folder are available for classroom demonstration. | `examples/project_idea.txt`, `outputs/demo_run/run.json`, `outputs/demo_run/WORKFLOW_LOG.md`, `outputs/demo_run/final_report.md`, `DEMO_SCRIPT.md`, `demo_materials/README.md` |
| Source repo | The standalone source workspace contains the runner, assignment core package, tests, docs, example input, dependency list, and generated demo output. | `run_council.py`, `assignment_core/`, `tests/`, `README.md`, `WORKFLOW_LOG.md`, `requirements.txt` |
| Submission preparation | The project includes a final verifier, clean packaging script, TXT generator, and course submission template so final packaging can be completed once the student ID and public link are known. | `final_check.py`, `create_submission_package.py`, `create_submission_txt.py`, `SUBMISSION_TEMPLATE.md`, `QA_CHECKLIST.md` |

## Remaining Gap Checklist

- [x] Decide whether the final interface will use Streamlit, Gradio, or a
  lightweight command-line demo only.
- [ ] Add final demo screenshots or a short demo video from the Streamlit interface.
- [ ] Re-run the test suite and demo command immediately before submission.
- [x] Add a final local verifier for required files and core output contract.
- [x] Add a clean zip packaging path excluding caches/logs/local-only files.
- [x] Add a required TXT generator for the final student-id-based submission file.
- [ ] Confirm whether the final recorded demo uses `api` mode or clearly labels
  `mock_test` as an offline fallback.
