import unittest
import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add parent directory to path to import app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the app module
import app

class TestAppCoreFunctions(unittest.TestCase):
    """Test core functions of the app without Streamlit runtime."""

    def test_get_mock_response_prompt_a(self):
        """Test deterministic mock response for Prompt A."""
        response = app.get_mock_response("A")
        self.assertEqual(response, app.MOCK_RESPONSES["default"]["response_a"])
        
        response = app.get_mock_response("prompt a")
        self.assertEqual(response, app.MOCK_RESPONSES["default"]["response_a"])
        
        response = app.get_mock_response("Prompt A")
        self.assertEqual(response, app.MOCK_RESPONSES["default"]["response_a"])

    def test_get_mock_response_prompt_b(self):
        """Test deterministic mock response for Prompt B."""
        response = app.get_mock_response("B")
        self.assertEqual(response, app.MOCK_RESPONSES["default"]["response_b"])
        
        response = app.get_mock_response("prompt b")
        self.assertEqual(response, app.MOCK_RESPONSES["default"]["response_b"])
        
        response = app.get_mock_response("Prompt B")
        self.assertEqual(response, app.MOCK_RESPONSES["default"]["response_b"])

    def test_get_mock_response_other(self):
        """Test deterministic mock response for other prompts."""
        response = app.get_mock_response("Some custom prompt")
        self.assertIn("Deterministic mock response", response)
        self.assertIn("hash", response.lower())
        
        # Test determinism: same input should give same output
        response2 = app.get_mock_response("Some custom prompt")
        self.assertEqual(response, response2)

    def test_generate_response_no_api_key(self):
        """Test generate_response without API key uses mock."""
        result = app.generate_response("Test prompt", "A", api_key=None)
        self.assertEqual(result["source"], "mock")
        self.assertEqual(result["model"], "mock")
        self.assertEqual(result["response"], app.MOCK_RESPONSES["default"]["response_a"])
        
        result = app.generate_response("Test prompt", "B", api_key="")
        self.assertEqual(result["source"], "mock")
        self.assertEqual(result["response"], app.MOCK_RESPONSES["default"]["response_b"])

    def test_generate_response_with_api_key(self):
        """Test generate_response with API key attempts API call."""
        # Mock the OpenAI call to avoid network access
        with patch('app.call_openai_api') as mock_call:
            mock_call.return_value = "Mocked API response"
            result = app.generate_response("Test prompt", "A", api_key="fake-key")
            self.assertEqual(result["source"], "api")
            self.assertEqual(result["model"], app.DEFAULT_MODEL)
            self.assertEqual(result["response"], "Mocked API response")
            mock_call.assert_called_once()

    def test_create_comparison_report(self):
        """Test comparison report creation."""
        task = "Test task"
        prompt_a = "Prompt A text"
        prompt_b = "Prompt B text"
        result_a = {
            "prompt": prompt_a,
            "response": "Response A",
            "source": "mock",
            "model": "mock",
            "temperature": 0.7,
            "max_tokens": 150,
            "timestamp": "2024-01-01T00:00:00"
        }
        result_b = {
            "prompt": prompt_b,
            "response": "Response B",
            "source": "mock",
            "model": "mock",
            "temperature": 0.7,
            "max_tokens": 150,
            "timestamp": "2024-01-01T00:00:00"
        }
        
        report = app.create_comparison_report(task, prompt_a, prompt_b, result_a, result_b)
        
        self.assertEqual(report["task"], task)
        self.assertEqual(report["prompt_a"], prompt_a)
        self.assertEqual(report["prompt_b"], prompt_b)
        self.assertEqual(report["response_a"], "Response A")
        self.assertEqual(report["response_b"], "Response B")
        self.assertEqual(report["source_a"], "mock")
        self.assertEqual(report["source_b"], "mock")
        self.assertIn("timestamp", report)

    def test_mock_responses_are_deterministic(self):
        """Test that mock responses are truly deterministic."""
        response1 = app.get_mock_response("A")
        response2 = app.get_mock_response("A")
        self.assertEqual(response1, response2)
        
        response1 = app.get_mock_response("B")
        response2 = app.get_mock_response("B")
        self.assertEqual(response1, response2)
        
        response1 = app.get_mock_response("Custom test prompt")
        response2 = app.get_mock_response("Custom test prompt")
        self.assertEqual(response1, response2)

    def test_mock_responses_different_for_a_and_b(self):
        """Test that mock responses for A and B are different."""
        response_a = app.get_mock_response("A")
        response_b = app.get_mock_response("B")
        self.assertNotEqual(response_a, response_b)

    def test_report_json_serializable(self):
        """Test that the report can be serialized to JSON."""
        task = "Test task"
        prompt_a = "Prompt A"
        prompt_b = "Prompt B"
        result_a = app.generate_response(prompt_a, "A", api_key=None)
        result_b = app.generate_response(prompt_b, "B", api_key=None)
        
        report = app.create_comparison_report(task, prompt_a, prompt_b, result_a, result_b)
        
        # Should not raise an exception
        json_str = json.dumps(report, indent=2)
        self.assertIsInstance(json_str, str)
        
        # Should be able to parse back
        parsed = json.loads(json_str)
        self.assertEqual(parsed["task"], task)

    def test_default_constants(self):
        """Test that default constants are properly defined."""
        self.assertEqual(app.DEFAULT_MODEL, "gpt-3.5-turbo")
        self.assertEqual(app.DEFAULT_TEMPERATURE, 0.7)
        self.assertEqual(app.DEFAULT_MAX_TOKENS, 150)
        self.assertIn("default", app.MOCK_RESPONSES)
        self.assertIn("response_a", app.MOCK_RESPONSES["default"])
        self.assertIn("response_b", app.MOCK_RESPONSES["default"])

if __name__ == '__main__':
    unittest.main()
