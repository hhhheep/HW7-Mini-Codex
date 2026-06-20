from __future__ import annotations

import streamlit as st


st.set_page_config(page_title="Generated AI Experiment App", layout="wide")
st.title("Generated AI Experiment App")
st.write("Build and validate a small generative-AI application from this task: Build a small Streamlit generative-AI prompt experiment app. The generated project should let a user record prompt variants, seed values, expected model behavior, and result notes. It should include a README, requirements file, and a basic validation test so the orchestrator can package and judge the result.")

prompt = st.text_area("Experiment prompt", "Compare two prompt variants for a generative AI demo.")
seed = st.number_input("Seed", value=42, step=1)

if st.button("Create experiment record"):
    st.subheader("Generated experiment record")
    st.json({
        "prompt": prompt,
        "seed": int(seed),
        "status": "recorded",
        "note": "Replace this stub with a real LLM or diffusion backend when credentials/GPU are available.",
    })
