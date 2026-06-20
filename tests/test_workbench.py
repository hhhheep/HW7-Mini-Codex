from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from assignment_core.workbench import (
    apply_changeset,
    collect_context,
    ensure_sample_workspace,
    propose_changes,
    restore_changeset_snapshot,
    zip_workspace,
)


class WorkbenchTest(unittest.TestCase):
    def test_mock_change_request_applies_and_validates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "workspace" / "generated_project"
            output = root / "outputs" / "workbench"
            ensure_sample_workspace(workspace, reset=True)

            proposal = propose_changes(
                "Add a generation history table that records each prompt and response.",
                workspace,
                output,
            )
            self.assertEqual(proposal["kind"], "mini_codex_proposal")
            self.assertTrue(any(item["path"] == "app.py" for item in proposal["changeset"]["files"]))
            self.assertTrue(proposal["diffs"])

            applied = apply_changeset(proposal["changeset"], workspace, output)
            self.assertEqual(applied["result"]["status"], "applied")
            self.assertTrue(all(item["success"] for item in applied["result"]["validations"]))
            self.assertIn("Generation history", (workspace / "app.py").read_text(encoding="utf-8"))

    def test_restore_snapshot_undoes_applied_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "workspace" / "generated_project"
            output = root / "outputs" / "workbench"
            ensure_sample_workspace(workspace, reset=True)
            original_app = (workspace / "app.py").read_text(encoding="utf-8")
            proposal = propose_changes(
                "Add a generation history table that records each prompt and response.",
                workspace,
                output,
            )
            applied = apply_changeset(proposal["changeset"], workspace, output)
            self.assertNotEqual(original_app, (workspace / "app.py").read_text(encoding="utf-8"))

            restored = restore_changeset_snapshot(applied, workspace, output)

            self.assertEqual(original_app, (workspace / "app.py").read_text(encoding="utf-8"))
            self.assertIn("app.py", restored["restored_files"])
            self.assertTrue((output / "restore_result.json").exists())
            self.assertTrue(all(item["success"] for item in restored["validations"]))

    def test_hash_mismatch_rejects_stale_patch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "workspace" / "generated_project"
            output = root / "outputs" / "workbench"
            ensure_sample_workspace(workspace, reset=True)
            proposal = propose_changes("Add a CSV export button for the generation history.", workspace, output)

            (workspace / "app.py").write_text("# changed by user\n", encoding="utf-8")
            applied = apply_changeset(proposal["changeset"], workspace, output)

            rejected_paths = {item["path"] for item in applied["result"]["rejected_files"]}
            self.assertIn("app.py", rejected_paths)
            self.assertIn("# changed by user", (workspace / "app.py").read_text(encoding="utf-8"))

    def test_empty_workspace_can_generate_new_python_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "workspace" / "empty_project"
            output = root / "outputs" / "workbench"
            workspace.mkdir(parents=True)

            proposal = propose_changes("Create a Python CLI project.", workspace, output)
            paths = {item["path"] for item in proposal["changeset"]["files"]}
            self.assertIn("main.py", paths)
            self.assertIn("tests/test_basic.py", paths)

            applied = apply_changeset(proposal["changeset"], workspace, output)
            self.assertEqual(applied["result"]["status"], "applied")
            self.assertTrue(all(item["success"] for item in applied["result"]["validations"]))
            self.assertTrue((workspace / "main.py").exists())

    def test_empty_workspace_can_generate_static_site_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "workspace" / "empty_site"
            output = root / "outputs" / "workbench"
            workspace.mkdir(parents=True)

            proposal = propose_changes("Create a static website.", workspace, output)
            paths = {item["path"] for item in proposal["changeset"]["files"]}

            self.assertIn("index.html", paths)
            self.assertIn("style.css", paths)
            self.assertIn("script.js", paths)

    def test_context_uses_hashes_for_editable_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace" / "generated_project"
            ensure_sample_workspace(workspace, reset=True)

            context = collect_context(workspace)

            paths = {item.path for item in context.selected_files}
            self.assertIn("app.py", paths)
            self.assertTrue(all(len(item.sha256) == 64 for item in context.selected_files))

    def test_zip_workspace_exports_editable_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "workspace" / "generated_project"
            output = root / "outputs"
            ensure_sample_workspace(workspace, reset=True)

            zip_path = zip_workspace(workspace, output)

            with zipfile.ZipFile(zip_path) as archive:
                names = set(archive.namelist())
            self.assertIn("app.py", names)
            self.assertIn("experiment_store.py", names)
            self.assertIn("tests/test_basic.py", names)
            self.assertFalse(any("__pycache__" in name for name in names))


if __name__ == "__main__":
    unittest.main()
