# LLM Prompt Comparison App

A Streamlit application for comparing two LLM prompt variants side by side.

## Features

- Input a task and two prompt variants
- Optional OpenAI API integration (when API key is provided)
- Deterministic mock responses when no API key is available
- Side-by-side comparison report
- Downloadable JSON report

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd llm-prompt-comparison
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   streamlit run app.py
   ```

## Usage

1. Open the app in your browser (default: http://localhost:8501)
2. (Optional) Enter your OpenAI API key in the sidebar for real API responses
3. Enter a task description
4. Enter two prompt variants (Prompt A and Prompt B)
5. Click "Compare Prompts"
6. View the comparison report with responses side by side
7. Download the report as JSON if needed

## Testing

Run tests with:
```bash
python -m unittest discover -s tests
```

Tests do not require network access or API keys.

## Project Structure

```
.
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── tests/
    └── test_basic.py  # Unit tests
```

## How It Works

- When an API key is provided, the app calls the OpenAI-compatible API
- When no API key is available, the app uses deterministic mock responses
- The comparison report includes prompts, model names, settings, and generated responses
- All responses are recorded with timestamps for reproducibility
