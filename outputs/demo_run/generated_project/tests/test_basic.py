from __future__ import annotations

import unittest
from pathlib import Path


class GeneratedProjectTest(unittest.TestCase):
    def test_required_files_exist(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.assertTrue((root / "app.py").exists())
        self.assertTrue((root / "requirements.txt").exists())
        self.assertTrue((root / "README.md").exists())


if __name__ == "__main__":
    unittest.main()
