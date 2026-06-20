# Generated AI Experiment App

## Objective

Build and validate a small generative-AI application from this task: Build a small Streamlit generative-AI prompt experiment app. The generated
project should let a user record prompt variants, seed values, expected model
behavior, and result notes. It should include a README, requirements file, and a
basic validation test so the orchestrator can package and judge the result.

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
