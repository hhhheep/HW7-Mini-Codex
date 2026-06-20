import streamlit as st
import os
import json
from datetime import datetime

# Try to import OpenAI, but don't fail if not installed
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Default model configuration
DEFAULT_MODEL = "gpt-3.5-turbo"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 150

# Deterministic mock responses for when no API key is available
MOCK_RESPONSES = {
    "default": {
        "response_a": "This is a deterministic mock response for Prompt A. The task would be addressed by focusing on key requirements and delivering a structured solution.",
        "response_b": "This is a deterministic mock response for Prompt B. The approach would involve analyzing the problem from multiple angles and providing a comprehensive answer."
    }
}

def get_mock_response(prompt_variant: str) -> str:
    """Generate a deterministic mock response based on the prompt variant."""
    if "prompt a" in prompt_variant.lower() or prompt_variant == "A":
        return MOCK_RESPONSES["default"]["response_a"]
    elif "prompt b" in prompt_variant.lower() or prompt_variant == "B":
        return MOCK_RESPONSES["default"]["response_b"]
    else:
        # Generate a deterministic response based on the prompt content
        import hashlib
        hash_obj = hashlib.md5(prompt_variant.encode())
        hash_hex = hash_obj.hexdigest()
        return f"Deterministic mock response for prompt with hash {hash_hex[:8]}. This is a fallback response generated without API access."

def call_openai_api(prompt: str, api_key: str, model: str = DEFAULT_MODEL, 
                    temperature: float = DEFAULT_TEMPERATURE, 
                    max_tokens: int = DEFAULT_MAX_TOKENS) -> str:
    """Call OpenAI-compatible API with the given prompt."""
    if not OPENAI_AVAILABLE:
        return "Error: OpenAI library not installed. Please install with: pip install openai"
    
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling API: {str(e)}"

def generate_response(prompt: str, prompt_variant_label: str, api_key: str = None) -> dict:
    """Generate a response using API if key available, otherwise use mock."""
    if api_key and api_key.strip():
        response_text = call_openai_api(prompt, api_key)
        source = "api"
    else:
        response_text = get_mock_response(prompt_variant_label)
        source = "mock"
    
    return {
        "prompt": prompt,
        "response": response_text,
        "source": source,
        "model": DEFAULT_MODEL if source == "api" else "mock",
        "temperature": DEFAULT_TEMPERATURE,
        "max_tokens": DEFAULT_MAX_TOKENS,
        "timestamp": datetime.now().isoformat()
    }

def create_comparison_report(task: str, prompt_a: str, prompt_b: str, 
                              result_a: dict, result_b: dict) -> dict:
    """Create a structured comparison report."""
    return {
        "task": task,
        "prompt_a": prompt_a,
        "prompt_b": prompt_b,
        "response_a": result_a["response"],
        "response_b": result_b["response"],
        "model_a": result_a["model"],
        "model_b": result_b["model"],
        "source_a": result_a["source"],
        "source_b": result_b["source"],
        "temperature": result_a["temperature"],
        "max_tokens": result_a["max_tokens"],
        "timestamp": datetime.now().isoformat()
    }

def main():
    st.set_page_config(page_title="LLM Prompt Comparison App", layout="wide")
    
    st.title("🤖 LLM Prompt Comparison App")
    st.markdown("Compare two prompt variants for the same task.")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input("OpenAI API Key (optional)", type="password", 
                                help="Leave empty to use deterministic mock responses")
        
        if api_key:
            st.success("API key provided - will use OpenAI API")
        else:
            st.info("No API key - using deterministic mock responses")
        
        st.divider()
        st.markdown("### Settings")
        model = st.text_input("Model", value=DEFAULT_MODEL, disabled=not bool(api_key))
        temperature = st.slider("Temperature", 0.0, 2.0, DEFAULT_TEMPERATURE, 0.1, disabled=not bool(api_key))
        max_tokens = st.number_input("Max Tokens", 50, 500, DEFAULT_MAX_TOKENS, disabled=not bool(api_key))
    
    # Main content area
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Task Description")
        task = st.text_area("Enter the task for the LLM:", height=100, 
                           placeholder="e.g., Write a short poem about AI")
    
    with col2:
        st.subheader("Comparison Settings")
        st.markdown("Enter two different prompt variants for the same task.")
    
    st.divider()
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Prompt Variant A")
        prompt_a = st.text_area("Enter Prompt A:", height=150, key="prompt_a",
                               placeholder="e.g., Write a creative poem about artificial intelligence")
    
    with col_b:
        st.subheader("Prompt Variant B")
        prompt_b = st.text_area("Enter Prompt B:", height=150, key="prompt_b",
                               placeholder="e.g., Compose a haiku about machine learning")
    
    # Compare button
    if st.button("Compare Prompts", type="primary", use_container_width=True):
        if not task.strip():
            st.error("Please enter a task description.")
        elif not prompt_a.strip() or not prompt_b.strip():
            st.error("Please enter both prompt variants.")
        else:
            with st.spinner("Generating responses..."):
                # Generate responses
                result_a = generate_response(prompt_a, "A", api_key)
                result_b = generate_response(prompt_b, "B", api_key)
                
                # Create comparison report
                report = create_comparison_report(task, prompt_a, prompt_b, result_a, result_b)
                
                # Store in session state for persistence
                st.session_state["last_report"] = report
                st.session_state["result_a"] = result_a
                st.session_state["result_b"] = result_b
    
    # Display results if available
    if "last_report" in st.session_state:
        report = st.session_state["last_report"]
        result_a = st.session_state["result_a"]
        result_b = st.session_state["result_b"]
        
        st.divider()
        st.header("📊 Comparison Report")
        
        # Metadata section
        with st.expander("Report Metadata", expanded=False):
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("Task", report["task"][:50] + "..." if len(report["task"]) > 50 else report["task"])
            with col_m2:
                st.metric("Temperature", report["temperature"])
            with col_m3:
                st.metric("Max Tokens", report["max_tokens"])
            
            st.markdown(f"**Timestamp:** {report['timestamp']}")
        
        # Response comparison
        col_r1, col_r2 = st.columns(2)
        
        with col_r1:
            st.subheader("Prompt A Response")
            st.markdown(f"**Source:** {'API' if result_a['source'] == 'api' else 'Mock'}")
            st.markdown(f"**Model:** {result_a['model']}")
            st.info(result_a["response"])
        
        with col_r2:
            st.subheader("Prompt B Response")
            st.markdown(f"**Source:** {'API' if result_b['source'] == 'api' else 'Mock'}")
            st.markdown(f"**Model:** {result_b['model']}")
            st.info(result_b["response"])
        
        # Full prompt display
        with st.expander("View Full Prompts"):
            st.markdown("### Prompt A")
            st.code(report["prompt_a"], language="text")
            st.markdown("### Prompt B")
            st.code(report["prompt_b"], language="text")
        
        # Download report
        report_json = json.dumps(report, indent=2)
        st.download_button(
            label="Download Report (JSON)",
            data=report_json,
            file_name=f"prompt_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

if __name__ == "__main__":
    main()
