import os
import streamlit as st
from dataclasses import dataclass, field
from typing import Optional, List

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ComparisonRecord:
    task: str
    prompt_a: str
    prompt_b: str
    model: str
    temperature: float
    max_tokens: int
    response_a: str
    response_b: str


# ---------------------------------------------------------------------------
# Core logic: response generation with fallback
# ---------------------------------------------------------------------------

def generate_response(prompt: str, model: str = "gpt-3.5-turbo",
                     temperature: float = 0.7, max_tokens: int = 150) -> str:
    """
    Generate a response for the given prompt.
    If OPENAI_API_KEY is set, call the OpenAI API.
    Otherwise, return a deterministic mock response.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[API Error] {str(e)}"
    else:
        # Deterministic mock response based on prompt content
        return f"Mock response for: {prompt[:50]}..."


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="LLM Prompt Comparison", layout="wide")
    st.title("LLM Prompt Comparison Tool")
    st.markdown("Compare two prompt variants for the same task.")

    # Initialize session state for storing records
    if "records" not in st.session_state:
        st.session_state.records = []

    # Input form
    with st.form("comparison_form"):
        task = st.text_area("Task Description",
                            placeholder="Describe the task you want the LLM to perform...")
        col1, col2 = st.columns(2)
        with col1:
            prompt_a = st.text_area("Prompt Variant A",
                                    placeholder="Enter first prompt variant...", height=150)
        with col2:
            prompt_b = st.text_area("Prompt Variant B",
                                    placeholder="Enter second prompt variant...", height=150)

        st.subheader("Model Settings")
        col3, col4, col5 = st.columns(3)
        with col3:
            model = st.selectbox("Model",
                                 ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"],
                                 index=0)
        with col4:
            temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
        with col5:
            max_tokens = st.number_input("Max Tokens", min_value=1, max_value=4096,
                                         value=150, step=10)

        submitted = st.form_submit_button("Compare Prompts")

    if submitted:
        if not task.strip() or not prompt_a.strip() or not prompt_b.strip():
            st.error("Please fill in all fields: task, prompt A, and prompt B.")
        else:
            with st.spinner("Generating responses..."):
                response_a = generate_response(prompt_a, model, temperature, max_tokens)
                response_b = generate_response(prompt_b, model, temperature, max_tokens)

            # Create and store record
            record = ComparisonRecord(
                task=task,
                prompt_a=prompt_a,
                prompt_b=prompt_b,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_a=response_a,
                response_b=response_b
            )
            st.session_state.records.append(record)

            # Display comparison report
            st.subheader("Comparison Report")
            col6, col7 = st.columns(2)
            with col6:
                st.markdown("### Prompt A")
                st.text(prompt_a)
                st.markdown("**Response A:**")
                st.write(response_a)
            with col7:
                st.markdown("### Prompt B")
                st.text(prompt_b)
                st.markdown("**Response B:**")
                st.write(response_b)

            st.markdown(f"**Model:** {model} | **Temperature:** {temperature} | **Max Tokens:** {max_tokens}")

    # Display history
    if st.session_state.records:
        with st.expander("View Comparison History"):
            for i, rec in enumerate(st.session_state.records, 1):
                st.markdown(f"### Comparison #{i}")
                st.markdown(f"**Task:** {rec.task}")
                col8, col9 = st.columns(2)
                with col8:
                    st.markdown(f"**Prompt A:** {rec.prompt_a}")
                    st.markdown(f"**Response A:** {rec.response_a}")
                with col9:
                    st.markdown(f"**Prompt B:** {rec.prompt_b}")
                    st.markdown(f"**Response B:** {rec.response_b}")
                st.markdown(f"**Model:** {rec.model} | **Temperature:** {rec.temperature} | **Max Tokens:** {rec.max_tokens}")
                st.divider()


if __name__ == "__main__":
    main()
