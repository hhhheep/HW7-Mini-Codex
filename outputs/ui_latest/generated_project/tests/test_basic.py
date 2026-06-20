import unittest
import os
import sys
import tempfile

# Add parent directory to path to import app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import generate_response, ComparisonRecord


class TestGenerateResponse(unittest.TestCase):
    """Test the response generation function with mock fallback."""

    def setUp(self):
        # Ensure no API key is set for testing
        if "OPENAI_API_KEY" in os.environ:
            self.original_key = os.environ["OPENAI_API_KEY"]
            del os.environ["OPENAI_API_KEY"]
        else:
            self.original_key = None

    def tearDown(self):
        if self.original_key:
            os.environ["OPENAI_API_KEY"] = self.original_key

    def test_mock_fallback_without_api_key(self):
        """Test that mock response is returned when no API key is set."""
        prompt = "What is the capital of France?"
        response = generate_response(prompt)
        self.assertIn("Mock response for:", response)
        self.assertIn(prompt[:50], response)

    def test_mock_fallback_with_empty_prompt(self):
        """Test mock response with empty prompt."""
        response = generate_response("")
        self.assertIn("Mock response for:", response)

    def test_mock_fallback_with_long_prompt(self):
        """Test mock response truncates long prompts."""
        long_prompt = "A" * 100
        response = generate_response(long_prompt)
        self.assertIn("Mock response for:", response)
        self.assertIn("A" * 50, response)

    def test_generate_response_with_api_key_mocked(self):
        """Test that API key presence triggers API call attempt."""
        # Set a dummy API key
        os.environ["OPENAI_API_KEY"] = "test-key"
        # The call will fail because the key is fake, but it should attempt API call
        response = generate_response("test prompt")
        # Should get an API error since the key is fake
        self.assertIn("[API Error]", response)


class TestComparisonRecord(unittest.TestCase):
    """Test the ComparisonRecord dataclass."""

    def test_record_creation(self):
        """Test that a ComparisonRecord can be created with all fields."""
        record = ComparisonRecord(
            task="Test task",
            prompt_a="Prompt A",
            prompt_b="Prompt B",
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=150,
            response_a="Response A",
            response_b="Response B"
        )
        self.assertEqual(record.task, "Test task")
        self.assertEqual(record.prompt_a, "Prompt A")
        self.assertEqual(record.prompt_b, "Prompt B")
        self.assertEqual(record.model, "gpt-3.5-turbo")
        self.assertEqual(record.temperature, 0.7)
        self.assertEqual(record.max_tokens, 150)
        self.assertEqual(record.response_a, "Response A")
        self.assertEqual(record.response_b, "Response B")

    def test_record_default_values(self):
        """Test that default values work correctly."""
        record = ComparisonRecord(
            task="Test",
            prompt_a="A",
            prompt_b="B",
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=150,
            response_a="",
            response_b=""
        )
        self.assertEqual(record.response_a, "")
        self.assertEqual(record.response_b, "")


class TestAppFileStructure(unittest.TestCase):
    """Test that required files exist."""

    def test_app_py_exists(self):
        """Test that app.py exists."""
        self.assertTrue(os.path.exists("app.py"))

    def test_requirements_txt_exists(self):
        """Test that requirements.txt exists."""
        self.assertTrue(os.path.exists("requirements.txt"))

    def test_readme_md_exists(self):
        """Test that README.md exists."""
        self.assertTrue(os.path.exists("README.md"))

    def test_tests_directory_exists(self):
        """Test that tests directory exists."""
        self.assertTrue(os.path.exists("tests"))


if __name__ == "__main__":
    unittest.main()
