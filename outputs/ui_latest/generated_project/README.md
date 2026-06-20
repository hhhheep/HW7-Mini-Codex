# LLM Prompt Comparison Tool

A Streamlit application for comparing two LLM prompt variants.

## Features

- Enter a task description and two prompt variants
- Optional OpenAI API integration (when API key is set)
- Deterministic mock fallback when no API key is available
- Records all comparisons with settings
- Displays side-by-side comparison report

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. (Optional) Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

3. Run the app:
   ```bash
   streamlit run app.py
   ```

## Testing

Run tests without network access or API keys:
```bash
python -m unittest discover -s tests
```

## Usage

1. Enter a task description
2. Enter two prompt variants (A and B)
3. Configure model settings (model, temperature, max tokens)
4. Click "Compare Prompts"
5. View the comparison report with both responses
6. Access comparison history via the expander
