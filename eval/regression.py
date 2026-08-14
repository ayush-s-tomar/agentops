"""
Eval regression detection.

Compares the latest eval score for an agent against a rolling baseline
(mean of the previous N scores). Flags a regression if the latest score
drops more than `threshold` below that baseline — this is the "catches
quality drops before deploy" feature.
"""

from tracer.db import fetch_eval_runs


def check_regression(agent_name: str, window: int = 5, threshold: float = 0.10):
    """
    Returns a dict:
      {
        "agent_name": str,
        "latest_score": float | None,
        "baseline": float | None,
        "regressed": bool,
        "message": str,
      }
    """
    runs = fetch_eval_runs(agent_name=agent_name, limit=window + 1)
    # fetch_eval_runs returns newest-first
    if not runs:
        return {
            "agent_name": agent_name,
            "latest_score": None,
            "baseline": None,
            "regressed": False,
            "message": "No eval runs recorded yet.",
        }

    latest = runs[0]["score"]
    history = [r["score"] for r in runs[1:]]

    if not history:
        return {
            "agent_name": agent_name,
            "latest_score": latest,
            "baseline": None,
            "regressed": False,
            "message": "Only one run recorded — no baseline yet.",
        }

    baseline = sum(history) / len(history)
    drop = baseline - latest
    regressed = drop > threshold

    message = (
        f"Latest score {latest:.2f} is {drop:.2f} below the {window}-run "
        f"baseline of {baseline:.2f}."
        if regressed
        else f"Latest score {latest:.2f} is within threshold of baseline {baseline:.2f}."
    )

    return {
        "agent_name": agent_name,
        "latest_score": latest,
        "baseline": baseline,
        "regressed": regressed,
        "message": message,
    }
