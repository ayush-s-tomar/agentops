"""
The @traced decorator — drop this on any function that makes an LLM call
or does agent work, and it logs latency, token usage, and estimated cost
to the AgentOps SQLite db automatically.

Usage:
    from tracer.trace import traced, set_run_context

    set_run_context(agent_name="SalesAgent")

    @traced(step_name="lead_research")
    def research_lead(url: str) -> dict:
        ...
        return result
"""

import functools
import time
import contextvars

from tracer.db import init_db, insert_trace, new_run_id

# Groq pricing (USD per 1M tokens) — update with your actual model/tier.
# These are placeholder rates; check console.groq.com/pricing for current numbers.
COST_PER_1M_TOKENS = {
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
    "default": {"input": 0.50, "output": 0.70},
}

_run_id_var = contextvars.ContextVar("run_id", default=None)
_agent_name_var = contextvars.ContextVar("agent_name", default="unnamed_agent")


def set_run_context(agent_name: str, run_id: str | None = None) -> str:
    """Call once at the start of an agent run. Returns the run_id in use."""
    init_db()
    rid = run_id or new_run_id()
    _run_id_var.set(rid)
    _agent_name_var.set(agent_name)
    return rid


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    rates = COST_PER_1M_TOKENS.get(model, COST_PER_1M_TOKENS["default"])
    return (input_tokens / 1_000_000) * rates["input"] + (
        output_tokens / 1_000_000
    ) * rates["output"]


def traced(step_name: str, model: str = "default"):
    """
    Decorator for a single agent step. If the wrapped function returns a
    dict containing 'input_tokens' / 'output_tokens' keys, cost is computed
    automatically. Otherwise those fields are logged as None.
    """

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            run_id = _run_id_var.get() or set_run_context(_agent_name_var.get())
            agent_name = _agent_name_var.get()
            started_at = time.time()
            status = "success"
            error_msg = None
            input_tokens = output_tokens = None
            cost = None

            try:
                result = fn(*args, **kwargs)
                if isinstance(result, dict):
                    input_tokens = result.get("input_tokens")
                    output_tokens = result.get("output_tokens")
                    if input_tokens is not None and output_tokens is not None:
                        cost = estimate_cost(model, input_tokens, output_tokens)
                return result
            except Exception as e:
                status = "error"
                error_msg = str(e)
                raise
            finally:
                duration_ms = (time.time() - started_at) * 1000
                insert_trace(
                    run_id=run_id,
                    agent_name=agent_name,
                    step_name=step_name,
                    started_at=started_at,
                    duration_ms=duration_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    estimated_cost_usd=cost,
                    status=status,
                    error=error_msg,
                )

        return wrapper

    return decorator
