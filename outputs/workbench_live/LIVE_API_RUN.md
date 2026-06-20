# Live API Mini-Codex Run

Target task:

```text
Add a CSV export button for the generation history.
```

Output directory:

```text
outputs/workbench_live/
```

Provider configuration:

- Base URL: `https://api.deepseek.com/v1`
- Discussion model: `deepseek-chat`
- Writer model: `deepseek-chat`
- API key: supplied through environment variable, not written to outputs

Result:

- `proposal.json` kind: `mini_codex_proposal`
- proposal mode: `api`
- `api_mode_used`: `true`
- `apply_result.json` kind: `mini_codex_apply`
- apply status: `applied`
- validations: all passed

Notes:

- The first local attempt failed because the `.env` value was quoted and the
  ad hoc PowerShell loader passed the surrounding quotes into the Bearer token.
- The successful run strips surrounding quotes before setting the process
  environment variable.
- No API key is stored in this evidence folder.
