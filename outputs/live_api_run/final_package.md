# Final Report

## Project

LLM Prompt Comparison App

## Objective

Build a Streamlit app that allows users to enter a task, compare two prompt variants, optionally call an OpenAI-compatible LLM API when an API key is available, and fall back to deterministic mock output when no key is available. The app should record prompt, model name, settings, generated responses, and produce a simple comparison report. The generated project must include app.py, requirements.txt, README.md, and unittest tests that do not require network access or API keys.

## Generated Files

- `app.py`
- `requirements.txt`
- `README.md`
- `tests/test_basic.py`

## Validation

- `python -m compileall generated_project` -> passed
- `python -m unittest discover -s tests` -> passed

## Judge

Pass status: `True`

The generated project fully satisfies the HW7 agentic workflow requirements. It includes a clear TaskSpec with objective, constraints, target stack, and success criteria. The architecture defines modules, data flow, file structure, and a detailed plan. The generated code (app.py) implements the Streamlit app with API call logic, deterministic mock fallback, comparison report generation, and download functionality. The project includes all required files: app.py, requirements.txt, README.md, and tests/test_basic.py. The tests pass without network access or API keys, covering mock responses, API fallback, report creation, and determinism. The validations confirm successful compilation and all 10 tests passing.

## Artifacts

- `generated_project/`
- `generated_project.zip`
- `WORKFLOW_LOG.md`
- `final_report.md`
