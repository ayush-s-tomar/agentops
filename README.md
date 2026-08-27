# AgentOps — LLM Observability & Eval Dashboard

![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-dashboard-FF4B4B?logo=streamlit&logoColor=white) ![Postgres](https://img.shields.io/badge/Supabase-Postgres-3ECF8E?logo=supabase&logoColor=white) ![Status](https://img.shields.io/badge/status-live-brightgreen)

**[Live Dashboard →](https://agentops-dashboard.streamlit.app/)**

Instruments LLM agents with tracing — latency, tokens, and cost per step —
stores run history in Postgres (Supabase), and surfaces it in a Streamlit
dashboard with automatic eval-regression flags when a prompt or model
change drops quality below a rolling baseline.

**TL;DR**
- 📡 **Traces a real production agent, not a demo** — [AgentLoop](https://agentloop.streamlit.app/)'s live runs feed this dashboard end-to-end; every number on it comes from an actual multi-step research agent in use, not synthetic sample data.
- 🚨 **Automatic regression detection** — flags when a prompt or model change drops an agent's own eval score below its rolling baseline, so quality drops surface on the dashboard instead of going unnoticed.
- 🔌 **Drop-in instrumentation** — one `@traced` decorator wraps any LLM-calling function; works with LangGraph or plain-Python agents, not tied to one framework.
- 🎯 **Built to plug into eval harnesses I already maintain**, not to replace them — see [Why build this instead of Langfuse/Helicone/Arize](#why-build-this-instead-of-using-langfusehelicionearize) below.

Currently instrumenting [AgentLoop](https://agentloop.streamlit.app/), a
live multi-step research agent — every real run is traced end-to-end
through this dashboard, not just synthetic example data.

## Why build this instead of using Langfuse/Helicone/Arize

Built to plug directly into eval harnesses I already maintain across my
other agents, rather than adopt a general-purpose platform — the
regression check compares against scores my own agents compute, not a
generic metric.

## Structure

```
agentops/
├── tracer/
│   ├── __init__.py
│   ├── db.py            # Postgres (Supabase) schema + insert/query helpers
│   └── trace.py         # @traced decorator — wrap any agent function/LLM call
├── eval/
│   └── regression.py    # compares latest eval score vs rolling baseline
├── dashboard/
│   └── app.py            # Streamlit dashboard (cost, latency, pass/fail trends)
├── examples/
│   └── example_agent.py  # shows how to instrument a Groq call with @traced
├── requirements.txt
└── .env.example
```

## Quick start

1. Create a free Supabase project (supabase.com) if you don't already have one.
2. From the project's **Connect** panel, grab the Transaction Pooler
   connection string, and drop the host/port/db/user/password into `.env`
   (see `.env.example`). Tables are created automatically on first run —
   no manual SQL needed.

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env         # add GROQ_API_KEY + Supabase DB credentials
python examples/example_agent.py   # generates a few sample traces
streamlit run dashboard/app.py
```

Data lives in Postgres, so it survives Streamlit Cloud redeploys — unlike
a local file, which would reset whenever the app restarts.

### Deploying

- Push this repo to GitHub, deploy `dashboard/app.py` on Streamlit Cloud.
- In the app's Settings → Secrets, paste the same key/value pairs from
  `.env` in TOML format. The dashboard bridges `st.secrets` into
  `os.environ` at startup, so no code changes are needed between local
  and deployed runs.

## Instrumenting a real agent

This is how [AgentLoop](https://agentloop.streamlit.app/) is wired in —
the same pattern applies to any LangGraph or plain-Python agent:

1. Copy `tracer/` into the target project's repo.
2. Wrap each LLM-calling function with `@traced`:

```python
from tracer.trace import traced, set_run_context

@traced(step_name="research", model="openai/gpt-oss-20b")
def research_node(state: AgentState) -> dict:
    ...
    return {**state, "input_tokens": ..., "output_tokens": ...}
```

3. Call `set_run_context(agent_name="YourAgent")` once at the start of a run.
4. At the end of a run, call `log_eval_score(run_id, agent_name, score)`
   with whatever eval metric the agent already computes.
5. Add the same Supabase credentials to that project's `.env` (and its
   Streamlit Cloud Secrets, if deployed) so both write to the same database.

## What this demonstrates

- Cost and latency tracing across multi-step agent runs, on a live
  production agent — not just a synthetic demo
- Automatic regression detection: flags when a prompt or model change
  drops eval scores below a rolling baseline, catching quality drops
  before they'd otherwise go unnoticed
- A real, deployed ops dashboard reading from a real Postgres database

## Known Limitations

- **Cost formula is a placeholder** — `tracer/trace.py` currently estimates cost from token counts using approximate pricing, not the exact per-model Groq pricing tiers; numbers on the dashboard are directionally correct, not billing-accurate yet.
- **Eval score being traced is itself a placeholder** in AgentLoop — the regression check is real and functional, but the quality signal it's watching isn't yet a robust report-quality metric (e.g., an LLM-as-judge score). The regression *mechanism* is proven; the metric it's protecting is the next thing to harden.
- **Single agent instrumented so far** — only AgentLoop is wired in today, so cross-agent cost/latency comparison (the next milestone below) isn't available yet.

## Next steps

- Instrument a second agent (SalesAgent or AskMyDocs) so the dashboard
  compares cost/latency across multiple production systems
- Swap the placeholder cost formula in `tracer/trace.py` for exact Groq
  pricing tiers as they're confirmed
- Replace the placeholder eval score in AgentLoop with a real metric
  (e.g. report-quality LLM-as-judge)

## Author

**Ayush Singh Tomar** — [GitHub](https://github.com/ayush-s-tomar)

Part of my AI developer portfolio — infrastructure for the agents themselves, not just another agent. See also: [AgentLoop](https://github.com/ayush-s-tomar/agentloop), the research agent this dashboard traces in production.
