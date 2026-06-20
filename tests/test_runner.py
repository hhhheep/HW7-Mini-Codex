from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from assignment_core.runner import run_workflow


class RunnerTest(unittest.TestCase):
    def test_run_workflow_writes_required_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "run"
            payload = run_workflow("Build a multi-agent generative app.", output_dir)
            self.assertEqual(payload["mode"], "mock_test")
            self.assertFalse(payload["api_packaged"])
            self.assertGreaterEqual(len(payload["agent_outputs"]), 3)
            self.assertTrue(payload["judge_report"]["pass_status"])
            self.assertTrue((output_dir / "run.json").exists())
            self.assertTrue((output_dir / "workflow_log.md").exists())
            self.assertTrue((output_dir / "final_package.md").exists())
            self.assertTrue((output_dir / "final_report.md").exists())
            self.assertTrue((output_dir / "generated_project.zip").exists())
            self.assertTrue((output_dir / "generated_project" / "app.py").exists())


if __name__ == "__main__":
    unittest.main()
