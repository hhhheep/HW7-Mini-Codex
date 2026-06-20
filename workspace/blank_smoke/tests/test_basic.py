from __future__ import annotations

import unittest

from experiment_store import create_record
from llm_client import generate_response


class BlankWorkspaceTest(unittest.TestCase):
    def test_response_is_deterministic(self) -> None:
        first = generate_response("hello", model_name="mock", temperature=0.2)
        second = generate_response("hello", model_name="mock", temperature=0.2)
        self.assertEqual(first, second)

    def test_record_keeps_fields(self) -> None:
        record = create_record("prompt", "response", model_name="mock")
        self.assertEqual(record["prompt"], "prompt")
        self.assertEqual(record["response"], "response")
        self.assertEqual(record["model_name"], "mock")


if __name__ == "__main__":
    unittest.main()
