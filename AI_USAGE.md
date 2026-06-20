# AI Usage Statement

Project title: Mini-Codex: Agentic Code Modification Workbench

## How AI Is Used

This project uses AI as a code-modification agent rather than as a hidden
one-shot file generator. The user selects a local workspace, describes a code
change in natural language, and the system asks an LLM-backed Patch Agent to
propose concrete file edits. The user reviews the proposal, inspects the diff,
and decides whether to apply, reject, or revise the change.

The primary workflow is:

```text
User request
  -> Context Loader
  -> Patch Agent
  -> Diff Review
  -> Human Apply
  -> Validator
  -> Repair if needed
  -> Preview
```

## Agent Responsibilities

The AI agent is responsible for:

- understanding the user's requested code change;
- reading a summarized context of the selected workspace;
- proposing file additions or full-file replacements;
- explaining the expected visible behavior;
- producing diffs for human review;
- suggesting repair patches when validation fails.

The AI agent is not allowed to silently modify files. The write step remains
human-gated through the UI.

## Human Responsibilities

The human user is responsible for:

- selecting or creating the workspace;
- entering the task request;
- reviewing the proposed diff;
- deciding whether to apply, reject, or revise the proposal;
- checking validation and preview results before submission.

## Live API and Mock Modes

The system provides two execution modes.

`mock_test` mode is deterministic and offline. It is used for repeatable tests,
final checks, and stable demo evidence when no network or API key is available.

`api` mode calls an OpenAI-compatible chat completion provider. In the submitted
live demo, the UI was configured with a DeepSeek-compatible endpoint and the
`deepseek-chat` model. The temporary API key was entered through the UI password
field and was not saved into source code, reports, screenshots, or the zip
package.

## Evidence Preserved

The project preserves evidence of AI use through:

- `outputs/workbench_latest/proposal.json`
- `outputs/workbench_latest/apply_result.json`
- `outputs/workbench_latest/WORKFLOW_LOG.md`
- `outputs/workbench_latest/chat_transcript.json`
- `outputs/workbench_live/` when a live API workbench run is saved
- `demo_materials/screenshots/` for the recorded UI walkthrough

The evidence records the selected mode, provider/model metadata, proposed
changes, generated diffs, apply result, validation status, and workflow notes.

## Safety and Reproducibility

API keys are not committed or packaged. The Live API configuration can be
provided through environment variables or the Streamlit UI for one run only.
The local workspace is restricted to the project-owned `workspace/` directory
so the demo can show real file modification while keeping the submitted package
reproducible and safe to inspect.

