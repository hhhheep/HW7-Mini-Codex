# Demo Script

Use this script to record the HW7 demonstration video or capture screenshots.

## Start the App

```powershell
cd <project-root>
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit, usually:

```text
http://localhost:8501
```

## Recording Flow

1. Show the app title: `Agentic Generative AI Experiment Orchestrator`.
2. Show the backend mode selector and model/provider fields.
3. Enter a generative-AI experiment task, such as a prompt comparison or RAG demo.
4. Run the workflow.
5. Open the `Task + Plan` tab and show Planner/Architect outputs.
6. Open `Generated Project` and show the actual generated files.
7. Open `Validation` and show compile/test stdout and status.
8. Open `Judge` and show pass/fail evaluation.
9. Open `Reports` and show downloads for `final_report.md`, `WORKFLOW_LOG.md`, and `generated_project.zip`.

For the strongest submission video, configure a provider key first and run `Live API`.
If no key is available during recording, label `Mock test` as the offline verification path.

## Required Screenshot Options

If submitting screenshots instead of video, capture:

- the input area before running;
- backend mode and model/provider fields;
- Planner or Architect structured output;
- at least one generated file under `generated_project/`;
- validation result;
- Judge result;
- report/zip download area.
