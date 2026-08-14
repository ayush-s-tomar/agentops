# AgentOps — LLM Observability & Eval Dashboard

Instruments your LLM agents with tracing (latency, tokens, cost per step),
stores run history in SQLite, and surfaces it in a Streamlit dashboard —
including automatic eval-regression flags when a prompt/model change drops
quality below a threshold.

## Structure

```
agentops/
├── tracer/
│   ├── __init__.py
│   ├── db.py           # SQLite schema + insert/query helpers
│   └── trace.py        # @traced decorator — wrap any agent function/LLM call
├── eval/
│   └── regression.py   # compares latest eval score vs rolling baseline
├── dashboard/
│   └── app.py           # Streamlit dashboard (cost, latency, pass/fail trends)
├── examples/
│   └── example_agent.py # shows how to instrument a Groq call with @traced
├── requirements.txt
└── .env.example
```

## Quick start

1. Create a free Supabase project (supabase.com) if you don't already have one.
2. Go to Project Settings → Database → Connection info, and copy the host,
   password, etc. into `.env` (see `.env.example`). Tables are created
   automatically on first run — no manual SQL needed.

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env         # add GROQ_API_KEY + Supabase DB credentials
python examples/example_agent.py   # generates a few sample traces
streamlit run dashboard/app.py
```

Data now persists in Postgres, so it survives Streamlit Cloud redeploys —
unlike a local SQLite file, which resets whenever the app restarts.

### Deploying

- Push this repo to GitHub, deploy `dashboard/app.py` on Streamlit Cloud.
- In Streamlit Cloud's app settings → Secrets, paste the same key/value
  pairs from your `.env` file (Streamlit reads `st.secrets`, but this repo
  also works if you set them as regular environment variables via the
  Streamlit Cloud "Secrets" TOML editor — they load through `os.environ`
  the same way).

## How to instrument YOUR existing agents (SalesAgent, AgentLoop, etc.)

1. Copy `tracer/` into that project's repo (or `pip install -e` this as a local package later).
2. Wrap any LLM call or tool call with the `@traced` decorator:

```python
from tracer.trace import traced

@traced(step_name="lead_research")
def research_lead(linkedin_url: str) -> dict:
    ...
    return result
```

3. At the end of a full agent run, call `log_eval_score(run_id, score)` with
   whatever eval metric you already compute (you have this logic in
   SalesAgent and AskMyDocs already — just call it and pass the score in).
4. Run the dashboard — it reads from `agentops.db` automatically.

## What this demonstrates on your resume

- Cost/latency tracing across multi-step agent runs
- Automatic regression detection: flags when a prompt/model change drops
  eval scores below a rolling baseline — catches quality drops before deploy
- A real ops dashboard, not just print statements

## Next steps to make it yours

- Swap the cost formula in `tracer/trace.py` for your actual Groq pricing tiers
- Point it at 2 of your real agents instead of the example
- Deploy the dashboard (Streamlit Cloud, same as your other projects)
- Add a GIF of the dashboard to your portfolio README, same pattern as
  AskMyDocs/SalesAgent
