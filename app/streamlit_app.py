from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pandas as pd
import streamlit as st

from smdebate.cli import run_item
from smdebate.config import load_config
from smdebate.lmstudio import create_local_chat_model
from smdebate.metrics import summarize_rows
from smdebate.storage import load_items

st.set_page_config(page_title="Same Model Debate Lab", layout="wide")

st.title("Same Model Debate Lab")
st.caption("Local LM Studio + LangChain experiment harness")

condition = st.selectbox(
    "Condition",
    ["independent", "debate_1r", "debate_3r_full_context"],
    index=1,
)
data_path = st.text_input("Dataset path", "data/smoke.jsonl")

config = load_config(condition=condition)

st.sidebar.header("Local LLM")
st.sidebar.write(f"Runtime: `{config.runtime}`")
st.sidebar.write(f"Base URL: `{config.base_url}`")
st.sidebar.write(f"Model: `{config.model_identifier}`")
st.sidebar.write(f"Family: `{config.model_family}`")
st.sidebar.write(f"Quantization: `{config.quantization}`")
st.sidebar.write(f"Reasoning mode: `{config.reasoning_mode}`")
st.sidebar.write(f"Agents: `{config.agent_count}`")
st.sidebar.write(f"Rounds: `{config.rounds}`")
st.sidebar.write(f"Temperature: `{config.temperature}`")

run = st.button("Run local experiment")

if run:
    items = load_items(Path(data_path))
    model = create_local_chat_model(config)

    rows = []
    progress = st.progress(0.0)

    for index, item in enumerate(items):
        rows.append(run_item(item=item, model=model, config=config))
        progress.progress((index + 1) / len(items))

    summary = summarize_rows(rows)

    st.subheader("Summary")
    st.json(asdict(summary))

    st.subheader("Rows")
    df = pd.DataFrame(
        [
            {
                "id": row["id"],
                "type": row["type"],
                "gold": row["gold"],
                "initial_answers": row["initial_answers"],
                "final_answers": row["final_answers"],
                "final_answer": row["final_answer"],
                "extraction_failures": row["extraction_failures"],
            }
            for row in rows
        ]
    )
    st.dataframe(df, use_container_width=True)
