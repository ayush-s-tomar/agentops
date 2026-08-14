"""
AgentOps dashboard — Streamlit UI.

Run with:  streamlit run dashboard/app.py
"""

import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

# Streamlit Cloud injects secrets into st.secrets, not os.environ — bridge
# them here so tracer/db.py (which reads os.environ) works unchanged both
# locally (.env file) and when deployed. Locally there's no secrets.toml at
# all, and newer Streamlit versions raise just from checking `in st.secrets`
# in that case — so this whole block is skipped safely with a try/except.
try:
    for key in (
        "SUPABASE_DB_HOST", "SUPABASE_DB_PORT", "SUPABASE_DB_NAME",
        "SUPABASE_DB_USER", "SUPABASE_DB_PASSWORD", "GROQ_API_KEY",
    ):
        if key in st.secrets and key not in os.environ:
            os.environ[key] = st.secrets[key]
except Exception:
    pass  # no secrets.toml locally — fine, .env / os.environ already has it

from tracer.db import fetch_traces, fetch_eval_runs, init_db
from eval.regression import check_regression

st.set_page_config(page_title="AgentOps Dashboard", layout="wide")
init_db()

st.title("AgentOps — LLM Observability Dashboard")
st.caption("Cost, latency, and eval-regression tracking for your agents.")

traces = fetch_traces(limit=1000)
eval_runs = fetch_eval_runs(limit=1000)

if not traces:
    st.info(
        "No traces yet. Run `python examples/example_agent.py` to generate "
        "sample data, or instrument your own agent with `@traced`."
    )
    st.stop()

df = pd.DataFrame(traces)
df["started_at_fmt"] = pd.to_datetime(df["started_at"], unit="s")

agents = sorted(df["agent_name"].unique())
selected_agent = st.sidebar.selectbox("Agent", ["All"] + agents)

if selected_agent != "All":
    df = df[df["agent_name"] == selected_agent]

# --- Top-line metrics ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total runs", df["run_id"].nunique())
col2.metric("Total steps traced", len(df))
col3.metric("Total est. cost", f"${df['estimated_cost_usd'].fillna(0).sum():.4f}")
error_rate = (df["status"] == "error").mean() * 100 if len(df) else 0
col4.metric("Error rate", f"{error_rate:.1f}%")

st.divider()

# --- Latency by step ---
st.subheader("Latency by step")
if not df.empty:
    latency_fig = px.box(
        df, x="step_name", y="duration_ms", points="all",
        labels={"duration_ms": "Duration (ms)", "step_name": "Step"},
    )
    st.plotly_chart(latency_fig, use_container_width=True)

# --- Cost over time ---
st.subheader("Cost per run over time")
cost_by_run = (
    df.groupby("run_id")
    .agg(started_at=("started_at", "min"), cost=("estimated_cost_usd", "sum"))
    .reset_index()
    .sort_values("started_at")
)
if not cost_by_run.empty:
    cost_by_run["started_at_fmt"] = pd.to_datetime(cost_by_run["started_at"], unit="s")
    cost_fig = px.line(cost_by_run, x="started_at_fmt", y="cost", markers=True,
                        labels={"started_at_fmt": "Run time", "cost": "Cost (USD)"})
    st.plotly_chart(cost_fig, use_container_width=True)

st.divider()

# --- Eval scores + regression check ---
st.subheader("Eval scores & regression detection")
if eval_runs:
    eval_df = pd.DataFrame(eval_runs)
    eval_df["created_at_fmt"] = pd.to_datetime(eval_df["created_at"], unit="s")

    for agent in (agents if selected_agent == "All" else [selected_agent]):
        result = check_regression(agent)
        badge = "🔴 REGRESSION" if result["regressed"] else "🟢 OK"
        st.write(f"**{agent}** — {badge}")
        st.caption(result["message"])

    score_fig = px.line(
        eval_df.sort_values("created_at"), x="created_at_fmt", y="score",
        color="agent_name", markers=True,
        labels={"created_at_fmt": "Time", "score": "Eval score"},
    )
    st.plotly_chart(score_fig, use_container_width=True)
else:
    st.info("No eval scores logged yet. Call `log_eval_score()` at the end of an agent run.")

st.divider()

# --- Raw trace table ---
st.subheader("Recent traces")
st.dataframe(
    df[["started_at_fmt", "agent_name", "step_name", "duration_ms",
        "input_tokens", "output_tokens", "estimated_cost_usd", "status"]]
    .sort_values("started_at_fmt", ascending=False)
    .head(100),
    use_container_width=True,
)