# Live API Testing

The app supports two modes:

- `api`: the normal model-backed mode. Planner, Architect, Coder, and Judge call an OpenAI-compatible `/chat/completions` endpoint.
- `mock_test`: local, reproducible, no network or API key required. This mode exists for unit tests and offline verification only.

API keys are never stored in the repository. Configure them as environment
variables before running the app or CLI.

The Streamlit UI also supports per-run Live API configuration. In `Live API`
mode, fill the provider preset, base URL, model names, and optional password
field. The password field is used only for the current run and is not written to
`run.json`, reports, workflow logs, or the submission zip. If the field is blank,
the app falls back to the selected environment variable, such as
`DEEPSEEK_API_KEY` or `DASHSCOPE_API_KEY`.

## Generic OpenAI-Compatible Configuration

```powershell
$env:HW7_LLM_API_KEY = "<YOUR_API_KEY>"
$env:HW7_LLM_BASE_URL = "https://api.openai.com/v1"
$env:HW7_DISCUSSION_MODEL = "gpt-4o-mini"
$env:HW7_WRITER_MODEL = "gpt-4o-mini"
python run_council.py --mode api --idea-file examples\project_idea.txt --output outputs\api_smoke
```

## OpenRouter-Compatible Example

```powershell
$env:OPENROUTER_API_KEY = "<YOUR_API_KEY>"
$env:HW7_DISCUSSION_MODEL = "openai/gpt-4o-mini"
$env:HW7_WRITER_MODEL = "openai/gpt-4o-mini"
python run_council.py --mode api --idea-file examples\project_idea.txt --output outputs\api_smoke
```

## DashScope/Qwen-Compatible Example

```powershell
$env:DASHSCOPE_API_KEY = "<YOUR_API_KEY>"
$env:HW7_DISCUSSION_MODEL = "qwen-plus"
$env:HW7_WRITER_MODEL = "qwen-plus"
python run_council.py --mode api --idea-file examples\project_idea.txt --output outputs\api_smoke
```

## DeepSeek-Compatible Example

```powershell
$env:DEEPSEEK_API_KEY = "<YOUR_API_KEY>"
$env:HW7_DISCUSSION_MODEL = "deepseek-chat"
$env:HW7_WRITER_MODEL = "deepseek-chat"
python run_council.py --mode api --idea-file examples\project_idea.txt --output outputs\api_smoke
```

The verified live evidence run in this package used a DeepSeek-compatible
OpenAI endpoint with `deepseek-chat` for Planner, Architect, Coder, and Judge.

## Model Roles

- Discussion model: Planner, Architect, and Judge structured reasoning.
- Writer model: Coder Agent file generation for `generated_project/`.

For a simple demo, both can use the same model. For a stronger demo, use a
general chat model for planning/judging and a coding-oriented model for generated files.

The run stores prompts, raw model responses, generated files, validation stdout/stderr,
and the judge report under the selected output directory. Do not include API keys in
submitted files or screenshots.
