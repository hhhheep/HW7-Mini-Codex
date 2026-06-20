from __future__ import annotations

import unittest

from experiment_store import create_record, get_history, clear_history
from llm_client import generate_response


class WorkspaceTest(unittest.TestCase):
    def setUp(self):
        clear_history()

    def test_mock_response_is_deterministic(self) -> None:
        first = generate_response("hello", model_name="mock", temperature=0.2)
        second = generate_response("hello", model_name="mock", temperature=0.2)
        self.assertEqual(first, second)

    def test_create_record_keeps_prompt_response_and_model(self) -> None:
        record = create_record("prompt", "response", model_name="mock")
        self.assertEqual(record["prompt"], "prompt")
        self.assertEqual(record["response"], "response")
        self.assertEqual(record["model_name"], "mock")

    def test_history_tracks_records(self) -> None:
        create_record("prompt1", "response1", model_name="mock")
        create_record("prompt2", "response2", model_name="mock")
        history = get_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["prompt"], "prompt1")
        self.assertEqual(history[1]["prompt"], "prompt2")

    def test_clear_history_removes_all_records(self) -> None:
        create_record("prompt1", "response1", model_name="mock")
        clear_history()
        self.assertEqual(len(get_history()), 0)


if __name__ == "__main__":
    unittest.main()
