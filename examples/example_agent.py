"""
Example: a tiny 2-step "agent" instrumented with @traced, so you can see
the dashboard populate with real-looking data before you wire this into
SalesAgent / AgentLoop.

Run:  python examples/example_agent.py
Then: streamlit run dashboard/app.py
"""

import sys
import random
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from tracer.trace import traced, set_run_context
from tracer.db import log_eval_score


@traced(step_name="research", model="llama-3.1-8b-instant")
def research_step(query: str) -> dict:
    time.sleep(random.uniform(0.2, 0.6))  # simulate API latency
    return {
        "input_tokens": random.randint(200, 500),
        "output_tokens": random.randint(100, 300),
        "content": f"Research notes for: {query}",
    }


@traced(step_name="draft_response", model="llama-3.3-70b-versatile")
def draft_step(notes: str) -> dict:
    time.sleep(random.uniform(0.3, 0.9))
    # occasionally simulate a failure so the dashboard shows error handling
    if random.random() < 0.1:
        raise RuntimeError("Simulated API timeout")
    return {
        "input_tokens": random.randint(300, 700),
        "output_tokens": random.randint(150, 400),
        "content": f"Drafted response based on: {notes[:30]}...",
    }


def run_agent_once(query: str):
    run_id = set_run_context(agent_name="ExampleAgent")
    try:
        research = research_step(query)
        draft = draft_step(research["content"])
        # pretend eval score: normally this comes from your existing eval harness
        score = round(random.uniform(0.65, 0.95), 2)
        log_eval_score(run_id=run_id, agent_name="ExampleAgent", score=score)
        print(f"[{run_id}] done — eval score {score}")
    except Exception as e:
        print(f"[{run_id}] failed — {e}")


if __name__ == "__main__":
    queries = [
        "AI adoption in fintech",
        "B2B SaaS pricing trends",
        "Sales agent lead scoring",
        "RAG evaluation benchmarks",
        "LangGraph multi-agent patterns",
    ]
    for q in queries:
        run_agent_once(q)

    print("\nDone. Run: streamlit run dashboard/app.py")
