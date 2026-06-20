from __future__ import annotations

import unittest

import app


class AppHelperTest(unittest.TestCase):
    def test_normalize_workspace_name_keeps_safe_local_name(self) -> None:
        self.assertEqual(app._normalize_workspace_name(" My New App! "), "My_New_App")
        self.assertEqual(app._normalize_workspace_name(" ../secret "), "secret")
        self.assertEqual(app._normalize_workspace_name("   "), "blank_workspace")

    def test_workspace_path_for_name_stays_under_workspace_base(self) -> None:
        path = app._workspace_path_for_name("../outside")
        self.assertEqual(path.parent.name, "workspace")
        self.assertEqual(path.name, "outside")

    def test_minimal_python_workspace_files_include_runnable_project_shape(self) -> None:
        files = app._minimal_python_workspace_files()
        self.assertIn("main.py", files)
        self.assertIn("README.md", files)
        self.assertIn("tests/test_basic.py", files)
        self.assertIn("python main.py", files["README.md"])

    def test_preview_entry_supports_streamlit_and_static_site(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            self.assertIsNone(app._preview_entry(workspace))
            (workspace / "index.html").write_text("<h1>Hello</h1>", encoding="utf-8")
            self.assertEqual(app._preview_entry(workspace), "index.html")
            (workspace / "app.py").write_text("print('hello')", encoding="utf-8")
            self.assertEqual(app._preview_entry(workspace), "app.py")

    def test_normalize_chat_request_trims_empty_composer_text(self) -> None:
        self.assertEqual(app._normalize_chat_request("  Add CSV export.  "), "Add CSV export.")
        self.assertEqual(app._normalize_chat_request(" \n\t "), "")

    def test_clean_api_key_strips_surrounding_quotes(self) -> None:
        self.assertEqual(app._clean_api_key(' "sk-test" '), "sk-test")
        self.assertEqual(app._clean_api_key(" 'sk-test' "), "sk-test")
        self.assertEqual(app._clean_api_key("sk-test"), "sk-test")

    def test_validations_pass_requires_nonempty_all_success(self) -> None:
        self.assertFalse(app._validations_pass([]))
        self.assertTrue(app._validations_pass([{"success": True}, {"success": True}]))
        self.assertFalse(app._validations_pass([{"success": True}, {"success": False}]))

    def test_repair_request_includes_failure_logs(self) -> None:
        proposal = {"user_message": "Add history table."}
        request = app._repair_request(
            proposal,
            [
                {
                    "command": "python -m unittest discover -s tests",
                    "stdout": "ran tests",
                    "stderr": "AssertionError: missing history",
                }
            ],
        )
        self.assertIn("Add history table.", request)
        self.assertIn("Repair request", request)
        self.assertIn("AssertionError", request)

    def test_thread_status_summarizes_chat_state(self) -> None:
        status = app._thread_status(
            {
                "messages": [{"role": "assistant", "content": "ready"}],
                "proposal": {"changeset": {}},
                "proposal_status": "draft",
                "apply_result": {
                    "result": {
                        "validations": [
                            {"success": True},
                            {"success": True},
                        ]
                    }
                },
                "preview": {"url": "http://localhost:8502"},
            }
        )
        self.assertEqual(status["proposal"], "Draft")
        self.assertEqual(status["validation"], "Pass")
        self.assertEqual(status["preview"], "Launched")
        self.assertEqual(status["messages"], "1")

    def test_next_change_suggestions_skip_completed_history_intent(self) -> None:
        suggestions = app._next_change_suggestions({"user_message": "Add a generation history table."})
        labels = [label for label, _ in suggestions]
        self.assertIn("Add CSV export", labels)
        self.assertIn("Improve UI", labels)
        self.assertNotIn("Add history", labels)

    def test_next_change_suggestions_skip_completed_export_intent(self) -> None:
        suggestions = app._next_change_suggestions({"user_message": "Add CSV export for history."})
        labels = [label for label, _ in suggestions]
        self.assertIn("Improve UI", labels)
        self.assertNotIn("Add CSV export", labels)

    def test_turn_timeline_waiting_state(self) -> None:
        items = app._turn_timeline_items({"messages": []})
        states = {item["step"]: item["state"] for item in items}
        self.assertEqual(states["Request"], "Waiting")
        self.assertEqual(states["Proposal"], "Waiting")
        self.assertEqual(states["Validation"], "Not run")
        self.assertEqual(states["Preview"], "Locked")

    def test_turn_timeline_applied_pass_state(self) -> None:
        items = app._turn_timeline_items(
            {
                "messages": [{"role": "user", "content": "Add a history table."}],
                "proposal": {"changeset": {"summary": "Adds generation history."}},
                "proposal_status": "applied",
                "apply_result": {
                    "result": {
                        "validations": [
                            {"success": True},
                            {"success": True},
                        ]
                    }
                },
            }
        )
        states = {item["step"]: item["state"] for item in items}
        self.assertEqual(states["Request"], "Ready")
        self.assertEqual(states["Proposal"], "Applied")
        self.assertEqual(states["Validation"], "Pass")
        self.assertEqual(states["Preview"], "Ready")

    def test_proposal_action_hint_for_draft(self) -> None:
        level, text = app._proposal_action_hint({"ready": True}, "draft", None)
        self.assertEqual(level, "info")
        self.assertIn("Apply", text)
        self.assertIn("Revise", text)

    def test_proposal_action_hint_for_stale_workspace(self) -> None:
        level, text = app._proposal_action_hint({"ready": False}, "draft", None)
        self.assertEqual(level, "warning")
        self.assertIn("regenerate", text.lower())

    def test_proposal_action_hint_for_failed_validation(self) -> None:
        level, text = app._proposal_action_hint(
            {"ready": True},
            "applied",
            {"result": {"validations": [{"success": False}]}},
        )
        self.assertEqual(level, "warning")
        self.assertIn("Repair with Agent", text)
        self.assertNotIn("launch the preview", text)

    def test_proposal_action_hint_for_passed_validation(self) -> None:
        level, text = app._proposal_action_hint(
            {"ready": True},
            "applied",
            {"result": {"validations": [{"success": True}]}},
        )
        self.assertEqual(level, "success")
        self.assertIn("launch the preview", text)

    def test_proposal_file_rows_marks_ready_stale_and_new_files(self) -> None:
        rows = app._proposal_file_rows(
            {
                "files": [
                    {"path": "app.py", "old_content_hash": "abc", "reason": "update UI"},
                    {"path": "README.md", "old_content_hash": "def", "reason": "update docs"},
                    {"path": "notes.txt", "old_content_hash": None, "reason": "add notes"},
                ]
            },
            {"stale_files": [{"path": "README.md"}]},
        )
        rows_by_file = {row["File"]: row for row in rows}
        self.assertEqual(rows_by_file["app.py"]["Status"], "ready")
        self.assertEqual(rows_by_file["README.md"]["Status"], "stale context")
        self.assertEqual(rows_by_file["notes.txt"]["Status"], "new file")
        self.assertEqual(rows_by_file["app.py"]["Reason"], "update UI")

    def test_proposal_run_rows_describe_live_api_without_key(self) -> None:
        rows = app._proposal_run_rows(
            {
                "api_mode_used": True,
                "created_at": "2026-06-19T22:52:26Z",
                "provider": {
                    "base_url": "https://api.example.test/v1",
                    "discussion_model": "discussion-model",
                    "writer_model": "writer-model",
                },
            }
        )
        values = {row["Field"]: row["Value"] for row in rows}
        self.assertEqual(values["Run mode"], "Live API")
        self.assertEqual(values["Discussion model"], "discussion-model")
        self.assertEqual(values["Writer model"], "writer-model")
        self.assertNotIn("key", " ".join(values.values()).lower())

    def test_proposal_run_rows_describe_mock_source(self) -> None:
        rows = app._proposal_run_rows({"api_mode_used": False, "provider": None})
        values = {row["Field"]: row["Value"] for row in rows}
        self.assertEqual(values["Run mode"], "Mock test")
        self.assertEqual(values["Model source"], "deterministic local mock")

    def test_api_readiness_rows_ready_with_env_key_source(self) -> None:
        rows = app._api_readiness_rows(
            base_url="https://api.example.test/v1",
            discussion_model="discussion",
            writer_model="writer",
            key_env="TEST_API_KEY",
            manual_key_present=False,
            env_key_available=True,
            use_env=True,
        )
        values = {row["Field"]: row["Value"] for row in rows}
        self.assertEqual(values["Live API readiness"], "ready")
        self.assertEqual(values["Missing"], "none")
        self.assertEqual(values["Key source"], "environment: TEST_API_KEY")
        self.assertNotIn("secret", " ".join(values.values()).lower())

    def test_api_readiness_rows_reports_missing_fields_without_env(self) -> None:
        rows = app._api_readiness_rows(
            base_url="",
            discussion_model="discussion",
            writer_model="",
            key_env="TEST_API_KEY",
            manual_key_present=False,
            env_key_available=False,
            use_env=True,
        )
        values = {row["Field"]: row["Value"] for row in rows}
        self.assertEqual(values["Live API readiness"], "incomplete")
        self.assertIn("base URL", values["Missing"])
        self.assertIn("writer model", values["Missing"])
        self.assertIn("API key in TEST_API_KEY", values["Missing"])

    def test_restore_summary_reports_restored_and_removed_files(self) -> None:
        summary = app._restore_summary(
            {
                "restored_files": ["app.py"],
                "removed_files": ["new_file.py"],
                "validations": [{"success": True}],
            }
        )
        self.assertIn("Undo Apply complete", summary)
        self.assertIn("app.py", summary)
        self.assertIn("new_file.py", summary)
        self.assertIn("passed", summary)


if __name__ == "__main__":
    unittest.main()
