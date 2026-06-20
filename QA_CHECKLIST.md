# QA and Submission Checklist

Use this checklist before demo recording, GitHub upload, and final submission.

## Commands to Run

- [ ] Install dependencies if needed:
  `python -m pip install -r requirements.txt`
- [ ] Run the automated tests:
  `python -m unittest discover -s tests`
- [ ] Regenerate the deterministic demo artifacts:
  `python run_council.py --mode mock_test --idea-file examples\project_idea.txt --output outputs\demo_run`
- [ ] If an API key is available, run one live model smoke test:
  `python run_council.py --mode api --idea-file examples\project_idea.txt --output outputs\api_smoke`
- [ ] Run the interactive UI:
  `streamlit run app.py`
- [ ] Or start the detached local demo:
  `python start_demo.py`
- [ ] Confirm the UI responds locally:
  `python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8501', timeout=8).status)"`
- [ ] Confirm the generated artifacts are readable:
  `Get-ChildItem outputs\demo_run`
- [ ] Run the final local verifier:
  `python final_check.py`
- [ ] Or run the Windows helper:
  `.\scripts\run_checks.ps1`
- [ ] Create a clean zip if needed:
  `python create_submission_package.py`
- [ ] Create the required TXT after the public link and demo filename are known:
  `python create_submission_txt.py --student-id <StudentID> --link <PUBLIC_LINK> --link-kind github --demo <StudentID>_HW7.mp4`

## Files That Must Exist

- [ ] `README.md`
- [ ] `app.py`
- [ ] `start_demo.py`
- [ ] `final_check.py`
- [ ] `create_submission_txt.py`
- [ ] `create_submission_package.py`
- [ ] `.streamlit\config.toml`
- [ ] `scripts\run_checks.ps1`
- [ ] `scripts\start_app.ps1`
- [ ] `scripts\build_package.ps1`
- [ ] `demo_materials\README.md`
- [ ] `SUBMISSION_TEMPLATE.md`
- [ ] `AGENT_ASSIGNMENT.md`
- [ ] `PROJECT_STATUS.md`
- [ ] `QA_CHECKLIST.md`
- [ ] `requirements.txt`
- [ ] `run_council.py`
- [ ] `examples\project_idea.txt`
- [ ] `assignment_core\__init__.py`
- [ ] `assignment_core\agents.py`
- [ ] `assignment_core\model_client.py`
- [ ] `assignment_core\schemas.py`
- [ ] `assignment_core\runner.py`
- [ ] `tests\test_runner.py`
- [ ] `outputs\demo_run\run.json`
- [ ] `outputs\demo_run\workflow_log.md`
- [ ] `outputs\demo_run\final_package.md`
- [ ] `outputs\demo_run\WORKFLOW_LOG.md`
- [ ] `outputs\demo_run\final_report.md`
- [ ] `outputs\demo_run\generated_project.zip`
- [ ] `outputs\demo_run\generated_project\app.py`
- [ ] `outputs\demo_run\generated_project\requirements.txt`
- [ ] `outputs\demo_run\generated_project\README.md`
- [ ] `outputs\demo_run\generated_project\tests\test_basic.py`
- [ ] `DEMO_SCRIPT.md`
- [ ] `API_TESTING.md`

## Forbidden Content Scan

- [ ] Search for credentials and private operational details:
  `rg -n -i "api[_-]?key|secret|token|password|credential|client_secret|ssh|gpu|mission|internal research|remote execution"`
- [ ] Resolve every hit before submission. Documentation may describe exclusions, but the submitted project should not include real secrets, private mission content, or operational instructions outside the assignment scope.
- [ ] Confirm no generated output claims live model/API execution unless that execution was actually performed and documented for the class submission.

## Demo Material Checklist

- [ ] Screenshot or short video shows the project idea input or example file.
- [ ] Demo shows the workflow command or UI entry point used to run the orchestrator.
- [ ] Demo shows backend/model configuration.
- [ ] Demo shows Planner, Architect, Coder, Runner/Collector, and Judge outputs.
- [ ] Demo shows generated files under `generated_project/`.
- [ ] Demo shows validation stdout/stderr and pass status.
- [ ] Demo shows report/log/zip downloads.
- [ ] If the demo uses `mock_test`, explicitly say it is the offline verification mode and not the claimed live model run.

## Final Submission File Checklist

- [ ] GitHub repository link or compressed project folder.
- [ ] Final README with setup, run, test, and demo instructions.
- [ ] Demo screenshot/video file or accessible link.
- [ ] Final submission text file required by the course platform.
- [ ] The text file follows `SUBMISSION_TEMPLATE.md`.
- [ ] Generated artifacts under `outputs\demo_run`.
- [ ] No caches, virtual environments, credentials, or unrelated local files included.
