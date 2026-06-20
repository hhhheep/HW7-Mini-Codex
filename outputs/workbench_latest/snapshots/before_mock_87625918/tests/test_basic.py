from __future__ import annotations

import unittest

from experiment_store import create_record, add_record, history_to_table
from llm_client import generate_response


class WorkspaceTest(unittest.TestCase):
    def test_mock_response_is_deterministic(self) -> None:
        first = generate_response("hello", model_name="mock", temperature=0.2)
        second = generate_response("hello", model_name="mock", temperature=0.2)
        self.assertEqual(first, second)

    def test_create_record_keeps_prompt_response_and_model(self) -> None:
        record = create_record("prompt", "response", model_name="mock")
        self.assertEqual(record["prompt"], "prompt")
        self.assertEqual(record["response"], "response")
        self.assertEqual(record["model_name"], "mock")

    def test_history_records_prompt_and_response(self) -> None:
        rows = add_record([], "prompt", "response", model_name="mock")
        table = history_to_table(rows)
        self.assertEqual(table[0]["prompt"], "prompt")
        self.assertEqual(table[0]["response"], "response")


if __name__ == "__main__":
    unittest.main()
