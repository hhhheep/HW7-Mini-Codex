from __future__ import annotations

import streamlit as st

from experiment_store import create_record
from llm_client import generate_response


st.set_page_config(page_title="Mini LLM Demo", layout="wide")
st.title("Mini LLM Demo")
st.write("Enter a task and generate a mock or API-backed LLM response.")

prompt = st.text_area("Task prompt", "Explain what an LLM agent does in one paragraph.")
model_name = st.text_input("Model name", "mock-local")
temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.1)
generate = st.button("Generate response")

response = ""
if generate:
    response = generate_response(prompt, model_name=model_name, temperature=temperature)
    st.subheader("Latest response")
    st.write(response)
else:
    st.info("Enter a task and click Generate response.")

latest_record = create_record(prompt, response, model_name=model_name)
st.caption(f"Current record model: {latest_record['model_name']}")

