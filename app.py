from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st

from assignment_core.model_client import ModelClientError, ModelConfig, load_model_config
from assignment_core.workbench import (
    DEFAULT_WORKSPACE,
    apply_changeset,
    collect_context,
    ensure_sample_workspace,
    launch_preview,
    propose_changes,
    restore_changeset_snapshot,
    validate_workspace,
    zip_workspace,
)


WORKSPACE_BASE = DEFAULT_WORKSPACE.parent
DEFAULT_WORKSPACE_NAME = DEFAULT_WORKSPACE.name
OUTPUT_DIR = Path("outputs/workbench_latest")
CHAT_TRANSCRIPT_MD = OUTPUT_DIR / "CHAT_TRANSCRIPT.md"
CHAT_TRANSCRIPT_JSON = OUTPUT_DIR / "chat_transcript.json"
EXAMPLES = {
    "History table": "Add a generation history table that records each prompt and response.",
    "CSV export": "Add a CSV export button for the generation history.",
    "Classroom UI": "Improve the UI so it looks more like a classroom demo instead of a developer tool.",
}
RUN_STATE_DEFAULTS = {
    "proposal": None,
    "proposal_status": "none",
    "apply_result": None,
    "restore_result": None,
    "preview": None,
    "manual_validations": None,
    "revision_mode": False,
}
PROVIDER_PRESETS = {
    "DeepSeek test default": {
        "base_url": "https://api.deepseek.com/v1",
        "discussion_model": "deepseek-chat",
        "writer_model": "deepseek-chat",
        "key_env": "DEEPSEEK_API_KEY",
    },
    "DashScope/Qwen": {
        "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        "discussion_model": "qwen-flash",
        "writer_model": "qwen3-coder-next",
        "key_env": "DASHSCOPE_API_KEY",
    },
    "OpenAI-compatible blank": {
        "base_url": "",
        "discussion_model": "",
        "writer_model": "",
        "key_env": "HW7_LLM_API_KEY",
    },
}


def main() -> None:
    st.set_page_config(page_title="Mini-Codex Workbench", layout="wide")
    _init_state()
    _ensure_active_workspace()

    st.title("Mini-Codex")

    nav_col, chat_col, inspector_col = st.columns([0.78, 1.42, 0.9], gap="large")
    with nav_col:
        runtime_config = _render_left_rail()

    with chat_col:
        _render_chat(runtime_config)

    with inspector_col:
        _render_inspector()

    _render_evidence_tabs()


def _init_state() -> None:
    st.session_state.setdefault("active_workspace_name", DEFAULT_WORKSPACE_NAME)
    st.session_state.setdefault("active_conversation", "demo")
    st.session_state.setdefault(
        "conversations",
        {
            "demo": {
                "title": "Generation history",
                "workspace": str(_workspace_root()),
                **RUN_STATE_DEFAULTS,
                "messages": [
                    {
                        "role": "assistant",
                        "content": "Workspace loaded. Ask for a code change and I will propose a diff before writing files.",
                    }
                ],
            }
        },
    )
    st.session_state.setdefault("revision_note", "")


def _ensure_active_workspace() -> None:
    root = _workspace_root()
    if not root.exists():
        ensure_sample_workspace(root)


def _workspace_root() -> Path:
    name = st.session_state.get("active_workspace_name", DEFAULT_WORKSPACE_NAME)
    return _workspace_path_for_name(str(name))


def _workspace_path_for_name(name: str) -> Path:
    safe_name = _normalize_workspace_name(name)
    base = WORKSPACE_BASE.resolve()
    target = (base / safe_name).resolve()
    try:
        target.relative_to(base)
    except ValueError as exc:
        raise ValueError("workspace must stay under the local workspace directory") from exc
    return target


def _workspace_names() -> list[str]:
    WORKSPACE_BASE.mkdir(parents=True, exist_ok=True)
    if not DEFAULT_WORKSPACE.exists():
        ensure_sample_workspace(DEFAULT_WORKSPACE)
    names = [path.name for path in WORKSPACE_BASE.iterdir() if path.is_dir()]
    if DEFAULT_WORKSPACE_NAME not in names:
        names.append(DEFAULT_WORKSPACE_NAME)
    return sorted(set(names), key=lambda item: (item != DEFAULT_WORKSPACE_NAME, item.lower()))


def _normalize_workspace_name(name: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", name.strip()).strip("._-")
    return (normalized or "blank_workspace")[:48]


def _next_workspace_name() -> str:
    existing = set(_workspace_names())
    index = 1
    while f"empty_workspace_{index}" in existing:
        index += 1
    return f"empty_workspace_{index}"


def _create_workspace(name: str, template: str) -> tuple[bool, str]:
    safe_name = _normalize_workspace_name(name)
    target = _workspace_path_for_name(safe_name)
    if target.exists():
        return False, f"`workspace/{safe_name}` already exists."
    if template == "Empty workspace":
        target.mkdir(parents=True, exist_ok=False)
    elif template == "Demo Streamlit starter":
        ensure_sample_workspace(target, reset=True)
    else:
        _write_blank_workspace(target)
    return True, safe_name


def _write_blank_workspace(target: Path) -> None:
    for rel_path, content in _minimal_python_workspace_files().items():
        path = target / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")


def _render_left_rail() -> ModelConfig | None:
    st.subheader("Workspaces")
    workspace_names = _workspace_names()
    active_name = st.session_state.get("active_workspace_name", DEFAULT_WORKSPACE_NAME)
    if active_name not in workspace_names:
        active_name = DEFAULT_WORKSPACE_NAME
        st.session_state["active_workspace_name"] = active_name
    selected_workspace = st.selectbox(
        "Selected workspace",
        workspace_names,
        index=workspace_names.index(active_name),
        format_func=lambda name: f"workspace/{name}",
    )
    if selected_workspace != active_name:
        st.session_state["active_workspace_name"] = selected_workspace
        _clear_active_run()
        _active_conversation()["workspace"] = str(_workspace_root())
        _append_message("assistant", f"Switched workspace to `workspace/{selected_workspace}`.")
        st.rerun()

    workspace_root = _workspace_root()
    st.caption(str(workspace_root))

    with st.expander("New workspace", expanded=False):
        with st.form("new_workspace_form"):
            new_name = st.text_input("Workspace name", value=_next_workspace_name())
            template = st.selectbox("Template", ["Empty workspace", "Demo Streamlit starter", "Minimal Python starter"])
            submitted = st.form_submit_button("Create workspace", use_container_width=True)
        if submitted:
            created, result = _create_workspace(new_name, template)
            if created:
                st.session_state["active_workspace_name"] = result
                _clear_active_run()
                _active_conversation()["workspace"] = str(_workspace_root())
                _append_message("assistant", f"Created `workspace/{result}` from `{template}`.")
                st.rerun()
            else:
                st.warning(result)

    context = collect_context(workspace_root)

    with st.expander("Files", expanded=True):
        for item in context.selected_files:
            st.write(f"`{item.path}` `{item.sha256[:8]}`")
        if context.selected_files:
            selected_file = st.selectbox(
                "Inspect file",
                [item.path for item in context.selected_files],
                key=f"selected_context_file_{workspace_root.name}",
            )
            selected_snapshot = next(item for item in context.selected_files if item.path == selected_file)
            st.code(selected_snapshot.content, language=_language_for(selected_snapshot.path))
        else:
            st.caption("No editable files yet. Ask Mini-Codex to create files in this workspace.")

    action_cols = st.columns(2)
    with action_cols[0]:
        if st.button("Reset Starter", use_container_width=True):
            ensure_sample_workspace(workspace_root, reset=True)
            _clear_active_run()
            _append_message("assistant", "Workspace reset to the starter LLM app.")
            st.rerun()
    with action_cols[1]:
        if st.button("Validate", use_container_width=True):
            validations = [item.model_dump() for item in validate_workspace(workspace_root)]
            _set_active_run_value("manual_validations", validations)
            _append_message("assistant", _validation_summary(validations))

    st.subheader("Chats")
    conversations = st.session_state["conversations"]
    active_key = st.session_state.get("active_conversation", "demo")
    for key, conversation in conversations.items():
        title = conversation.get("title", key)
        active_marker = ">" if key == active_key else ""
        label = f"{active_marker} {title}".strip()
        if st.button(label, key=f"chat_select_{key}", use_container_width=True):
            st.session_state["active_conversation"] = key
            _persist_chat_transcript()
            st.rerun()
        st.caption(_chat_list_caption(conversation))
    if st.button("New chat", use_container_width=True):
        key = f"chat_{len(conversations) + 1}"
        conversations[key] = {
            "title": "Untitled change",
            "workspace": str(workspace_root),
            **RUN_STATE_DEFAULTS,
            "messages": [
                {
                    "role": "assistant",
                    "content": "New change thread opened. Describe the next code modification.",
                }
            ],
        }
        st.session_state["active_conversation"] = key
        _clear_active_run()
        _persist_chat_transcript()
        st.rerun()

    st.subheader("Model")
    mode_label = st.radio("Mode", ["Mock test", "Live API"], horizontal=True)
    st.session_state["mode"] = "api" if mode_label == "Live API" else "mock_test"
    if st.session_state["mode"] == "api":
        return _render_live_api_config()
    st.caption("Mock test is deterministic offline evidence.")
    return None


def _render_chat(runtime_config: ModelConfig | None) -> None:
    st.subheader(_active_conversation()["title"])
    st.caption("Request -> proposal -> diff -> apply -> validation -> preview")
    _render_thread_status_bar(_active_conversation())
    _render_turn_timeline(_active_conversation())

    for message in _active_conversation()["messages"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    example_cols = st.columns(3)
    for index, (label, prompt) in enumerate(EXAMPLES.items()):
        with example_cols[index]:
            if st.button(label, key=f"example_{label}", use_container_width=True):
                _run_agent_turn(prompt, runtime_config)
                st.rerun()

    _render_chat_composer(runtime_config)

    proposal = _active_run_value("proposal")
    if proposal:
        st.divider()
        _render_proposal_card(proposal)


def _render_chat_composer(runtime_config: ModelConfig | None) -> None:
    active_key = st.session_state.get("active_conversation", "demo")
    with st.form(f"chat_composer_{active_key}", clear_on_submit=True):
        user_message = st.text_area(
            "Message Mini-Codex",
            height=120,
            placeholder="Describe the code change you want. Example: Add CSV export for the prompt history.",
        )
        submitted = st.form_submit_button("Run Agent", type="primary", use_container_width=True)
    if submitted:
        request = _normalize_chat_request(user_message)
        if not request:
            st.warning("Write a request before running the agent.")
            return
        _run_agent_turn(request, runtime_config)
        st.rerun()


def _render_proposal_card(proposal: dict[str, Any]) -> None:
    changeset = proposal["changeset"]
    readiness = _proposal_readiness(proposal)
    st.markdown(f"**Proposed change:** {changeset['summary']}")
    st.write(changeset["expected_visible_change"])
    st.caption(f"Status: {_active_run_value('proposal_status') or 'draft'}")
    st.dataframe(_proposal_run_rows(proposal), hide_index=True, use_container_width=True)
    if readiness["ready"]:
        st.success("Workspace context matches this proposal.")
    else:
        st.warning("Workspace changed since this proposal was generated. Regenerate before applying.")
        for item in readiness["stale_files"]:
            st.caption(f"`{item['path']}` expected `{item['expected']}`, current `{item['actual']}`")

    files = ", ".join(f"`{item['path']}`" for item in changeset["files"])
    st.markdown(f"**Files:** {files}")
    st.dataframe(_proposal_file_rows(changeset, readiness), hide_index=True, use_container_width=True)
    hint_level, hint_text = _proposal_action_hint(
        readiness,
        _active_run_value("proposal_status"),
        _active_run_value("apply_result"),
    )
    if hint_level == "success":
        st.success(hint_text)
    elif hint_level == "warning":
        st.warning(hint_text)
    else:
        st.info(hint_text)

    for index, item in enumerate(proposal["diffs"]):
        expanded = index == 0 or item["path"] in {"app.py", "index.html", "main.py"}
        with st.expander(f"Diff: {item['path']}", expanded=expanded):
            st.code(item["diff"] or "(no textual difference)", language="diff")

    apply_col, revise_col, reject_col = st.columns(3)
    with apply_col:
        apply_disabled = _active_run_value("proposal_status") == "applied" or not readiness["ready"]
        if st.button("Apply", type="primary", disabled=apply_disabled, use_container_width=True):
            with st.spinner("Writing files and validating..."):
                result = apply_changeset(changeset, _workspace_root(), OUTPUT_DIR)
            _set_active_run_value("apply_result", result)
            _set_active_run_value("proposal_status", "applied")
            _set_active_run_value("revision_mode", False)
            _append_message("assistant", _apply_summary(result))
            st.rerun()
    with revise_col:
        if st.button("Revise", use_container_width=True):
            _set_active_run_value("revision_mode", True)
            _append_message("assistant", "Tell me what to change about this proposal, and I will regenerate a new diff.")
            st.rerun()
    with reject_col:
        if st.button("Reject", use_container_width=True):
            _set_active_run_value("proposal", None)
            _set_active_run_value("apply_result", None)
            _set_active_run_value("proposal_status", "rejected")
            _set_active_run_value("revision_mode", False)
            _append_message("assistant", "Proposal rejected. Send another request when ready.")
            st.rerun()

    if _active_run_value("revision_mode"):
        revision_note = st.text_area(
            "Revision instruction",
            key="revision_note",
            height=92,
            placeholder="Example: keep the history in a helper module, add a test for empty history, or avoid changing README.",
        )
        if st.button("Regenerate Proposal", disabled=not revision_note.strip(), use_container_width=True):
            revised_request = _revised_request(proposal["user_message"], revision_note)
            _run_agent_turn(revised_request, _runtime_config_from_state())
            _set_active_run_value("revision_mode", False)
            st.session_state["revision_note"] = ""
            st.rerun()
    elif not readiness["ready"]:
        if st.button("Regenerate from Current Workspace", use_container_width=True):
            _run_agent_turn(proposal["user_message"], _runtime_config_from_state())
            st.rerun()
    _render_continue_actions(proposal)


def _render_thread_status_bar(conversation: dict[str, Any]) -> None:
    status = _thread_status(conversation)
    cols = st.columns(4)
    cols[0].metric("Proposal", status["proposal"])
    cols[1].metric("Validation", status["validation"])
    cols[2].metric("Preview", status["preview"])
    cols[3].metric("Messages", status["messages"])


def _render_turn_timeline(conversation: dict[str, Any]) -> None:
    items = _turn_timeline_items(conversation)
    cols = st.columns(len(items))
    for index, item in enumerate(items):
        with cols[index]:
            st.markdown(f"**{item['step']}**")
            st.caption(item["state"])
            st.write(item["detail"])


def _render_continue_actions(proposal: dict[str, Any]) -> None:
    apply_result = _active_run_value("apply_result")
    if _active_run_value("proposal_status") != "applied":
        return
    if not apply_result or not _validations_pass(apply_result["result"]["validations"]):
        return

    suggestions = _next_change_suggestions(proposal)
    if not suggestions:
        return

    st.markdown("**Continue editing**")
    cols = st.columns(len(suggestions))
    for index, (label, prompt) in enumerate(suggestions):
        with cols[index]:
            if st.button(label, key=f"continue_{index}_{label}", use_container_width=True):
                _run_agent_turn(prompt, _runtime_config_from_state())
                st.rerun()


def _render_inspector() -> None:
    st.subheader("Inspector")
    proposal = _active_run_value("proposal")
    apply_result = _active_run_value("apply_result")

    if proposal:
        changeset = proposal["changeset"]
        st.metric("Proposed files", len(changeset["files"]))
        for item in changeset["files"]:
            st.write(f"`{item['path']}`")
    else:
        st.info("No active proposal.")

    st.divider()
    st.subheader("Validation")
    if apply_result:
        result = apply_result["result"]
        st.metric("Apply status", result["status"])
        validation_ready = _validations_pass(result["validations"])
        st.metric("Validation", "Pass" if validation_ready else "Needs repair")
        _render_validations(result["validations"])
        failed_validations = [item for item in result["validations"] if not item.get("success")]
        if failed_validations:
            if st.button("Repair with Agent", type="primary", use_container_width=True):
                repair_request = _repair_request(_active_run_value("proposal"), failed_validations)
                _append_message("assistant", "Validation failed. I will use the failing logs to propose a repair.")
                _run_agent_turn(repair_request, _runtime_config_from_state())
                st.rerun()
        if st.button("Undo Apply", use_container_width=True):
            restore_result = restore_changeset_snapshot(apply_result, _workspace_root(), OUTPUT_DIR)
            _set_active_run_value("restore_result", restore_result)
            _set_active_run_value("apply_result", None)
            _set_active_run_value("proposal_status", "draft")
            _set_active_run_value("preview", None)
            _append_message("assistant", _restore_summary(restore_result))
            st.rerun()
    elif _active_run_value("manual_validations"):
        _render_validations(_active_run_value("manual_validations"))
    else:
        st.caption("Validation appears after Apply or Validate.")

    st.divider()
    preview_ready = bool(apply_result) and _validations_pass(apply_result["result"]["validations"])
    preview_entry = _preview_entry(_workspace_root())
    if st.button("Launch Preview on 8502", disabled=not preview_ready or preview_entry is None, use_container_width=True):
        try:
            preview = launch_preview(_workspace_root(), OUTPUT_DIR)
        except ValueError as exc:
            _append_message("assistant", f"Preview is not available yet: {exc}")
            st.rerun()
        else:
            _set_active_run_value("preview", preview)
            _append_message("assistant", f"Preview launched: {preview['url']}")
            st.rerun()
    if apply_result and not preview_ready:
        st.caption("Preview is available after validation passes.")
    elif preview_ready and preview_entry is None:
        st.caption("Preview needs `app.py` for Streamlit or `index.html` for a static site.")
    preview = _active_run_value("preview")
    if preview:
        st.link_button("Open preview", preview["url"], use_container_width=True)
        st.caption(f"PID {preview['pid']}")


def _render_validations(validations: list[dict]) -> None:
    for item in validations:
        label = "Pass" if item["success"] else "Fail"
        st.markdown(f"**{label}:** `{item['command']}`")
        with st.expander("Logs", expanded=not item["success"]):
            if item.get("stdout"):
                st.code(item["stdout"], language="text")
            if item.get("stderr"):
                st.code(item["stderr"], language="text")


def _render_evidence_tabs() -> None:
    tabs = st.tabs(["Current Files", "Evidence", "Downloads"])
    with tabs[0]:
        context = collect_context(_workspace_root())
        for item in context.selected_files:
            with st.expander(item.path, expanded=item.path in {"app.py", "index.html", "main.py"}):
                st.code(item.content, language=_language_for(item.path))

    with tabs[1]:
        if _active_run_value("proposal"):
            st.subheader("Proposal JSON")
            st.json(_active_run_value("proposal"))
        if _active_run_value("apply_result"):
            st.subheader("Apply Result JSON")
            st.json(_active_run_value("apply_result"))
        if _active_run_value("restore_result"):
            st.subheader("Restore Result JSON")
            st.json(_active_run_value("restore_result"))
        if not _active_run_value("proposal") and not _active_run_value("apply_result") and not _active_run_value("restore_result"):
            st.caption("No evidence yet.")

    with tabs[2]:
        workflow_log = _read_output("WORKFLOW_LOG.md")
        proposal_json = _read_output("proposal.json")
        apply_json = _read_output("apply_result.json")
        restore_json = _read_output("restore_result.json")
        transcript_md = _read_output("CHAT_TRANSCRIPT.md")
        transcript_json = _read_output("chat_transcript.json")
        workspace_zip = zip_workspace(_workspace_root(), OUTPUT_DIR)
        workspace_zip_bytes = workspace_zip.read_bytes()
        st.download_button("Download WORKFLOW_LOG.md", workflow_log, file_name="WORKFLOW_LOG.md", disabled=not workflow_log)
        st.download_button("Download proposal.json", proposal_json, file_name="proposal.json", disabled=not proposal_json)
        st.download_button("Download apply_result.json", apply_json, file_name="apply_result.json", disabled=not apply_json)
        st.download_button("Download restore_result.json", restore_json, file_name="restore_result.json", disabled=not restore_json)
        st.download_button("Download CHAT_TRANSCRIPT.md", transcript_md, file_name="CHAT_TRANSCRIPT.md", disabled=not transcript_md)
        st.download_button("Download chat_transcript.json", transcript_json, file_name="chat_transcript.json", disabled=not transcript_json)
        st.download_button("Download current_workspace.zip", workspace_zip_bytes, file_name="current_workspace.zip")


def _run_agent_turn(user_message: str, runtime_config: ModelConfig | None) -> None:
    mode = st.session_state.get("mode", "mock_test")
    if mode == "api" and runtime_config is None:
        _append_message("assistant", "Live API is selected, but model configuration is incomplete.")
        return
    _append_message("user", user_message)
    try:
        with st.spinner("Mini-Codex is reading the workspace and writing a patch proposal..."):
            proposal = propose_changes(user_message, _workspace_root(), OUTPUT_DIR, mode=mode, model_config=runtime_config)
    except ModelClientError as exc:
        _append_message("assistant", f"Live API failed: {exc}")
        return
    _set_active_run_value("proposal", proposal)
    _set_active_run_value("proposal_status", "draft")
    _set_active_run_value("apply_result", None)
    _set_active_run_value("restore_result", None)
    _set_active_run_value("preview", None)
    _set_active_run_value("manual_validations", None)
    _active_conversation()["title"] = _short_title(user_message)
    _append_message("assistant", _proposal_summary(proposal))


def _proposal_summary(proposal: dict[str, Any]) -> str:
    changeset = proposal["changeset"]
    files = ", ".join(item["path"] for item in changeset["files"])
    return f"I prepared a patch proposal: {changeset['summary']}\n\nFiles: {files}\n\nReview the diff below before applying."


def _apply_summary(apply_payload: dict[str, Any]) -> str:
    result = apply_payload["result"]
    validation_ok = all(item["success"] for item in result["validations"])
    files = ", ".join(result["applied_files"]) or "none"
    status = "passed" if validation_ok else "needs repair"
    return f"Applied files: {files}\n\nValidation {status}."


def _restore_summary(restore_payload: dict[str, Any]) -> str:
    restored = ", ".join(restore_payload.get("restored_files", [])) or "none"
    removed = ", ".join(restore_payload.get("removed_files", [])) or "none"
    validation_ok = _validations_pass(restore_payload.get("validations", []))
    status = "passed" if validation_ok else "needs attention"
    return f"Undo Apply complete.\n\nRestored files: {restored}\nRemoved new files: {removed}\n\nValidation {status}."


def _validation_summary(validations: list[dict]) -> str:
    status = "passed" if _validations_pass(validations) else "failed"
    return f"Manual validation {status}."


def _thread_status(conversation: dict[str, Any]) -> dict[str, str]:
    proposal = conversation.get("proposal")
    apply_result = conversation.get("apply_result")
    preview = conversation.get("preview")
    proposal_status = conversation.get("proposal_status", "none")
    if not proposal:
        proposal_label = "None"
    elif proposal_status == "applied":
        proposal_label = "Applied"
    elif proposal_status == "rejected":
        proposal_label = "Rejected"
    else:
        proposal_label = "Draft"

    if apply_result:
        validations = apply_result.get("result", {}).get("validations", [])
        validation_label = "Pass" if _validations_pass(validations) else "Needs repair"
    elif conversation.get("manual_validations"):
        validation_label = "Pass" if _validations_pass(conversation["manual_validations"]) else "Fail"
    else:
        validation_label = "Not run"

    return {
        "proposal": proposal_label,
        "validation": validation_label,
        "preview": "Launched" if preview else "Not launched",
        "messages": str(len(conversation.get("messages", []))),
    }


def _turn_timeline_items(conversation: dict[str, Any]) -> list[dict[str, str]]:
    messages = conversation.get("messages", [])
    last_request = next(
        (str(message.get("content", "")) for message in reversed(messages) if message.get("role") == "user"),
        "",
    )
    proposal = conversation.get("proposal")
    apply_result = conversation.get("apply_result")
    preview = conversation.get("preview")

    if proposal:
        proposal_state = "Applied" if conversation.get("proposal_status") == "applied" else "Draft"
        proposal_detail = proposal.get("changeset", {}).get("summary", "Patch proposal ready.")
    else:
        proposal_state = "Waiting"
        proposal_detail = "No diff yet."

    if apply_result:
        validations = apply_result.get("result", {}).get("validations", [])
        validation_state = "Pass" if _validations_pass(validations) else "Needs repair"
        validation_detail = f"{len(validations)} checks recorded."
    elif conversation.get("manual_validations"):
        validations = conversation["manual_validations"]
        validation_state = "Pass" if _validations_pass(validations) else "Fail"
        validation_detail = f"{len(validations)} manual checks recorded."
    else:
        validation_state = "Not run"
        validation_detail = "Apply or validate the workspace."

    preview_ready = bool(apply_result) and _validations_pass(apply_result.get("result", {}).get("validations", []))
    preview_state = "Launched" if preview else ("Ready" if preview_ready else "Locked")
    preview_detail = preview.get("url", "Waiting for passing validation.") if preview else "Available after validation passes."

    return [
        {
            "step": "Request",
            "state": "Ready" if last_request else "Waiting",
            "detail": _short_title(last_request) if last_request else "Describe the code change.",
        },
        {"step": "Proposal", "state": proposal_state, "detail": proposal_detail},
        {"step": "Validation", "state": validation_state, "detail": validation_detail},
        {"step": "Preview", "state": preview_state, "detail": preview_detail},
    ]


def _validations_pass(validations: list[dict]) -> bool:
    return bool(validations) and all(item.get("success") for item in validations)


def _next_change_suggestions(proposal: dict[str, Any]) -> list[tuple[str, str]]:
    previous_request = proposal.get("user_message", "").lower()
    suggestions: list[tuple[str, str]] = []
    if "csv" not in previous_request and "export" not in previous_request:
        suggestions.append(("Add CSV export", EXAMPLES["CSV export"]))
    if "classroom" not in previous_request and "ui" not in previous_request:
        suggestions.append(("Improve UI", EXAMPLES["Classroom UI"]))
    if "history" not in previous_request:
        suggestions.append(("Add history", EXAMPLES["History table"]))
    return suggestions[:3]


def _proposal_action_hint(
    readiness: dict[str, Any],
    proposal_status: str | None,
    apply_result: dict[str, Any] | None,
) -> tuple[str, str]:
    if not readiness.get("ready", False):
        return (
            "warning",
            "Next action: regenerate this proposal from the current workspace before applying.",
        )
    if proposal_status != "applied":
        return (
            "info",
            "Next action: review the diff, then choose Apply, Revise, or Reject.",
        )
    validations = (apply_result or {}).get("result", {}).get("validations", [])
    if _validations_pass(validations):
        return (
            "success",
            "Next action: launch the preview, download evidence, or continue editing.",
        )
    return (
        "warning",
        "Next action: use Repair with Agent from the Inspector before launching preview.",
    )


def _proposal_file_rows(changeset: dict[str, Any], readiness: dict[str, Any]) -> list[dict[str, str]]:
    stale_paths = {item.get("path", "") for item in readiness.get("stale_files", [])}
    rows: list[dict[str, str]] = []
    for item in changeset.get("files", []):
        path = item.get("path", "")
        if path in stale_paths:
            status = "stale context"
        elif item.get("old_content_hash"):
            status = "ready"
        else:
            status = "new file"
        rows.append(
            {
                "File": path,
                "Status": status,
                "Reason": item.get("reason", ""),
            }
        )
    return rows


def _proposal_run_rows(proposal: dict[str, Any]) -> list[dict[str, str]]:
    provider = proposal.get("provider") or {}
    mode = "Live API" if proposal.get("api_mode_used") else "Mock test"
    rows = [
        {"Field": "Run mode", "Value": mode},
        {"Field": "Created", "Value": str(proposal.get("created_at", ""))},
    ]
    if provider:
        rows.extend(
            [
                {"Field": "Base URL", "Value": str(provider.get("base_url", ""))},
                {"Field": "Discussion model", "Value": str(provider.get("discussion_model", ""))},
                {"Field": "Writer model", "Value": str(provider.get("writer_model", ""))},
            ]
        )
    else:
        rows.append({"Field": "Model source", "Value": "deterministic local mock"})
    return rows


def _api_readiness_rows(
    *,
    base_url: str,
    discussion_model: str,
    writer_model: str,
    key_env: str,
    manual_key_present: bool,
    env_key_available: bool,
    use_env: bool,
) -> list[dict[str, str]]:
    missing = []
    if not base_url.strip():
        missing.append("base URL")
    if not discussion_model.strip():
        missing.append("discussion model")
    if not writer_model.strip():
        missing.append("writer model")

    key_source = "manual input" if manual_key_present else "none"
    if not manual_key_present and use_env and env_key_available:
        key_source = f"environment: {key_env}"
    elif not manual_key_present and use_env and key_env:
        missing.append(f"API key in {key_env}")
    elif not manual_key_present and not use_env:
        missing.append("API key")

    ready = not missing
    return [
        {"Field": "Live API readiness", "Value": "ready" if ready else "incomplete"},
        {"Field": "Missing", "Value": ", ".join(missing) if missing else "none"},
        {"Field": "Key source", "Value": key_source},
    ]


def _preview_entry(workspace_root: Path) -> str | None:
    if (workspace_root / "app.py").exists():
        return "app.py"
    if (workspace_root / "index.html").exists():
        return "index.html"
    return None


def _clean_api_key(value: str) -> str:
    return value.strip().strip('"').strip("'").strip()


def _proposal_readiness(proposal: dict[str, Any]) -> dict[str, Any]:
    context = collect_context(_workspace_root())
    current_hashes = {item.path: item.sha256 for item in context.selected_files}
    stale_files = []
    for replacement in proposal.get("changeset", {}).get("files", []):
        expected = replacement.get("old_content_hash")
        if not expected:
            continue
        actual = current_hashes.get(replacement.get("path"), "<missing>")
        if actual != expected:
            stale_files.append(
                {
                    "path": replacement.get("path", ""),
                    "expected": str(expected)[:8],
                    "actual": str(actual)[:8],
                }
            )
    return {"ready": not stale_files, "stale_files": stale_files}


def _chat_list_caption(conversation: dict[str, Any]) -> str:
    proposal_status = conversation.get("proposal_status", "none")
    apply_status = (conversation.get("apply_result") or {}).get("result", {}).get("status")
    message_count = len(conversation.get("messages", []))
    parts = [f"{message_count} messages"]
    if proposal_status != "none":
        parts.append(f"proposal {proposal_status}")
    if apply_status:
        parts.append(f"apply {apply_status}")
    return " / ".join(parts)


def _append_message(role: str, content: str) -> None:
    _active_conversation()["messages"].append({"role": role, "content": content})
    _persist_chat_transcript()


def _clear_active_run() -> None:
    conversation = _active_conversation()
    for key, value in RUN_STATE_DEFAULTS.items():
        conversation[key] = value
    st.session_state["revision_note"] = ""
    _persist_chat_transcript()


def _revised_request(original_request: str, revision_note: str) -> str:
    return (
        f"{original_request.strip()}\n\n"
        f"Revision request: {revision_note.strip()}\n"
        "Regenerate the patch proposal to follow the revision request."
    )


def _repair_request(proposal: dict[str, Any] | None, failed_validations: list[dict]) -> str:
    original_request = (proposal or {}).get("user_message", "Repair the current workspace.")
    failure_notes = []
    for item in failed_validations:
        failure_notes.append(
            "\n".join(
                [
                    f"Command: {item.get('command', '')}",
                    f"Stdout: {item.get('stdout', '')[-1200:]}",
                    f"Stderr: {item.get('stderr', '')[-1600:]}",
                ]
            )
        )
    return (
        f"{original_request.strip()}\n\n"
        "Repair request: validation failed after applying the previous patch. "
        "Generate a new patch proposal that fixes the failure while preserving the requested behavior.\n\n"
        + "\n\n".join(failure_notes)
    )


def _runtime_config_from_state() -> ModelConfig | None:
    if st.session_state.get("mode") != "api":
        return None
    base_url = st.session_state.get("api_base_url", "").strip()
    discussion_model = st.session_state.get("api_discussion_model", "").strip()
    writer_model = st.session_state.get("api_writer_model", "").strip()
    key_env = st.session_state.get("api_key_env", "").strip()
    api_key = _clean_api_key(st.session_state.get("api_key_value", ""))
    if not api_key and st.session_state.get("api_use_env", True):
        api_key = _clean_api_key(os.getenv(key_env, ""))
    if not api_key and st.session_state.get("api_use_env", True):
        try:
            env_config = load_model_config()
        except ModelClientError:
            env_config = None
        if env_config is not None:
            api_key = env_config.api_key
    if not base_url or not discussion_model or not writer_model or not api_key:
        return None
    return ModelConfig(
        base_url=base_url.rstrip("/"),
        api_key=api_key,
        discussion_model=discussion_model,
        writer_model=writer_model,
    )


def _active_conversation() -> dict[str, Any]:
    conversations = st.session_state["conversations"]
    key = st.session_state.get("active_conversation", "demo")
    if key not in conversations:
        key = "demo"
        st.session_state["active_conversation"] = key
    conversation = conversations[key]
    for field, default in RUN_STATE_DEFAULTS.items():
        conversation.setdefault(field, default)
    return conversation


def _active_run_value(field: str) -> Any:
    return _active_conversation().get(field, RUN_STATE_DEFAULTS.get(field))


def _set_active_run_value(field: str, value: Any) -> None:
    _active_conversation()[field] = value
    _persist_chat_transcript()


def _persist_chat_transcript() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    conversations = st.session_state.get("conversations", {})
    safe_payload = {
        "schema_version": 1,
        "kind": "mini_codex_chat_transcript",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "active_conversation": st.session_state.get("active_conversation", "demo"),
        "conversations": {
            key: {
                "title": value.get("title", key),
                "workspace": value.get("workspace", str(_workspace_root())),
                "proposal_status": value.get("proposal_status", "none"),
                "apply_status": (value.get("apply_result") or {}).get("result", {}).get("status"),
                "message_count": len(value.get("messages", [])),
                "messages": value.get("messages", []),
            }
            for key, value in conversations.items()
        },
    }
    CHAT_TRANSCRIPT_JSON.write_text(json.dumps(safe_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    CHAT_TRANSCRIPT_MD.write_text(_render_chat_transcript_md(safe_payload), encoding="utf-8")


def _render_chat_transcript_md(payload: dict[str, Any]) -> str:
    lines = [
        "# Mini-Codex Chat Transcript",
        "",
        f"- Updated: {payload['updated_at']}",
        f"- Active conversation: `{payload['active_conversation']}`",
        "",
    ]
    for key, conversation in payload["conversations"].items():
        lines.extend(
            [
                f"## {conversation['title']}",
                "",
                f"- Conversation id: `{key}`",
                f"- Workspace: `{conversation['workspace']}`",
                f"- Proposal status: `{conversation['proposal_status']}`",
                f"- Apply status: `{conversation.get('apply_status') or 'none'}`",
                "",
            ]
        )
        for message in conversation.get("messages", []):
            lines.extend([f"### {message.get('role', 'message')}", "", str(message.get("content", "")).strip(), ""])
    return "\n".join(lines).rstrip() + "\n"


def _short_title(text: str) -> str:
    words = " ".join(text.strip().split())
    return words[:36] + ("..." if len(words) > 36 else "")


def _normalize_chat_request(text: str) -> str:
    return text.strip()


def _minimal_python_workspace_files() -> dict[str, str]:
    return {
        "main.py": """from __future__ import annotations


def summarize(text: str) -> str:
    normalized = " ".join(text.strip().split()) or "empty input"
    return f"Mini-Codex workspace: {normalized}"


if __name__ == "__main__":
    print(summarize("ready"))
""",
        "README.md": """# Minimal Python Workspace

This workspace was created from the minimal Python starter in the Mini-Codex workbench.

## Run

```powershell
python main.py
```

## Test

```powershell
python -m unittest discover -s tests
```
""",
        "tests/test_basic.py": """from __future__ import annotations

import unittest

from main import summarize


class MinimalPythonWorkspaceTest(unittest.TestCase):
    def test_summarize_includes_input(self) -> None:
        self.assertIn("hello", summarize("hello"))


if __name__ == "__main__":
    unittest.main()
""",
    }


def _render_live_api_config() -> ModelConfig | None:
    _init_api_config_state()
    shortcut_cols = st.columns(3)
    with shortcut_cols[0]:
        if st.button("DeepSeek"):
            _apply_api_preset("DeepSeek test default")
    with shortcut_cols[1]:
        if st.button("Qwen"):
            _apply_api_preset("DashScope/Qwen")
    with shortcut_cols[2]:
        if st.button("Clear API"):
            _clear_api_config()

    st.selectbox("Provider preset", list(PROVIDER_PRESETS), key="api_preset")
    use_env = st.checkbox("Use environment key when API key field is blank", value=True, key="api_use_env")
    base_url = st.text_input("Base URL", key="api_base_url")
    discussion_model = st.text_input("Discussion model", key="api_discussion_model")
    writer_model = st.text_input("Writer model", key="api_writer_model")
    key_env = st.text_input("Fallback key env var", key="api_key_env")
    api_key = st.text_input("API key for this run", value="", type="password", key="api_key_value")
    env_key_available = bool(_clean_api_key(os.getenv(key_env, ""))) if key_env else False
    st.dataframe(
        _api_readiness_rows(
            base_url=base_url,
            discussion_model=discussion_model,
            writer_model=writer_model,
            key_env=key_env,
            manual_key_present=bool(_clean_api_key(api_key)),
            env_key_available=env_key_available,
            use_env=use_env,
        ),
        hide_index=True,
        use_container_width=True,
    )

    if not base_url or not discussion_model or not writer_model:
        st.info("Fill Base URL and model names before running Live API.")
        return None
    resolved_key = _clean_api_key(api_key)
    if not resolved_key and use_env:
        resolved_key = _clean_api_key(os.getenv(key_env, ""))
    if not resolved_key and use_env:
        try:
            env_config = load_model_config()
        except ModelClientError:
            env_config = None
        if env_config is not None:
            resolved_key = env_config.api_key
    if not resolved_key:
        st.warning("No API key is available yet.")
        return None
    st.caption(f"Live API config: {base_url} | {discussion_model} / {writer_model}")
    return ModelConfig(
        base_url=base_url.rstrip("/"),
        api_key=resolved_key,
        discussion_model=discussion_model,
        writer_model=writer_model,
    )


def _init_api_config_state() -> None:
    if "api_preset" not in st.session_state:
        st.session_state["api_preset"] = "DeepSeek test default"
    preset = PROVIDER_PRESETS[st.session_state["api_preset"]]
    st.session_state.setdefault("api_base_url", os.getenv("HW7_LLM_BASE_URL", preset["base_url"]))
    st.session_state.setdefault("api_discussion_model", os.getenv("HW7_DISCUSSION_MODEL", preset["discussion_model"]))
    st.session_state.setdefault("api_writer_model", os.getenv("HW7_WRITER_MODEL", preset["writer_model"]))
    st.session_state.setdefault("api_key_env", preset["key_env"])
    st.session_state.setdefault("api_key_value", "")


def _apply_api_preset(name: str) -> None:
    preset = PROVIDER_PRESETS[name]
    st.session_state["api_preset"] = name
    st.session_state["api_base_url"] = preset["base_url"]
    st.session_state["api_discussion_model"] = preset["discussion_model"]
    st.session_state["api_writer_model"] = preset["writer_model"]
    st.session_state["api_key_env"] = preset["key_env"]
    st.session_state["api_key_value"] = ""


def _clear_api_config() -> None:
    st.session_state["api_preset"] = "OpenAI-compatible blank"
    st.session_state["api_base_url"] = ""
    st.session_state["api_discussion_model"] = ""
    st.session_state["api_writer_model"] = ""
    st.session_state["api_key_env"] = "HW7_LLM_API_KEY"
    st.session_state["api_key_value"] = ""


def _read_output(filename: str) -> str:
    path = OUTPUT_DIR / filename
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _language_for(path: str) -> str:
    if path.endswith(".py"):
        return "python"
    if path.endswith(".md"):
        return "markdown"
    if path.endswith(".json"):
        return "json"
    return "text"


if __name__ == "__main__":
    main()
