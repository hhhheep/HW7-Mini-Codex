from __future__ import annotations

import csv
import io

import streamlit as st

from experiment_store import create_record, get_history, clear_history
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

# Display generation history
st.subheader("Generation History")
history = get_history()
if history:
    st.write(f"Total records: {len(history)}")
    for i, rec in enumerate(history):
        with st.expander(f"Record {i+1}: {rec['model_name']} - {rec['created_at']}"):
            st.write(f"**Prompt:** {rec['prompt']}")
            st.write(f"**Response:** {rec['response']}")
            st.write(f"**Model:** {rec['model_name']}")
            st.write(f"**Created at:** {rec['created_at']}")

    # CSV export button
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=["prompt", "response", "model_name", "created_at"])
    writer.writeheader()
    for rec in history:
        writer.writerow(rec)
    csv_data = csv_buffer.getvalue()

    st.download_button(
        label="Export history as CSV",
        data=csv_data,
        file_name="generation_history.csv",
        mime="text/csv",
    )
else:
    st.info("No generation history yet.")

# Clear history button (optional, for testing)
if st.button("Clear history"):
    clear_history()
    st.rerun()
