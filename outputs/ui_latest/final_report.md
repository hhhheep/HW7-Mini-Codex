# Final Report

## Project

LLM Prompt Comparison Streamlit App

## Objective

Build a Streamlit application that allows users to enter a task, compare two prompt variants, optionally call an OpenAI-compatible LLM API when an API key is available, and fall back to deterministic mock output when no key is available. The app must record prompt, model name, settings, generated responses, and produce a simple comparison report. The generated project must include app.py, requirements.txt, README.md, and unittest tests that do not require network access or API keys.

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

The generated project fully satisfies the HW7 agentic workflow requirements. It includes a clear TaskSpec, a well-structured architecture, complete generated code (app.py, requirements.txt, README.md, tests/test_basic.py), successful validation (compile and test pass), all required artifacts, and is ready for reporting. The app handles missing API keys gracefully with deterministic mock output, records all inputs/outputs, and tests run without network access or API keys.

## Artifacts

- `generated_project/`
- `generated_project.zip`
- `WORKFLOW_LOG.md`
- `final_report.md`
