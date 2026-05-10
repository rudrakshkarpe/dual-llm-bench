from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from dual_llm_bench import AgentTrace


def run_trace_to_agent_trace(run_trace: Any) -> AgentTrace:
    """Convert the PyCon demo app's RunTrace model into a benchmark AgentTrace."""
    decision = run_trace.decision
    tool_request = None
    if decision.tool_request is not None:
        tool_request = {
            "name": decision.tool_request.name,
            "arguments": decision.tool_request.arguments,
            "rationale": decision.tool_request.rationale,
        }

    return AgentTrace(
        sample_id=run_trace.scenario_id,
        raw_input=run_trace.raw_input,
        privileged_input=run_trace.privileged_input,
        quarantined_output=(
            run_trace.quarantined_output.model_dump()
            if run_trace.quarantined_output is not None
            else None
        ),
        tool_request=tool_request,
        policy_verdict=run_trace.policy_verdict.status.value,
        final_outcome=run_trace.final_user_outcome,
        latency_ms=sum(llm_trace.latency_ms for llm_trace in run_trace.llm_traces),
        metadata={
            "mode": run_trace.mode.value,
            "scenario_title": run_trace.scenario_title,
            "run_backend": run_trace.run_backend,
            "decision": decision.model_dump(),
            "policy_verdict": run_trace.policy_verdict.model_dump(),
            "llm_traces": [llm_trace.model_dump() for llm_trace in run_trace.llm_traces],
        },
    )


def trace_dict_to_agent_trace(payload: Mapping[str, Any]) -> AgentTrace:
    """Convert a serialized demo RunTrace dictionary into AgentTrace."""
    decision = payload["decision"]
    tool_request = decision.get("tool_request")
    policy_verdict = payload["policy_verdict"]
    llm_traces = payload.get("llm_traces", [])
    latency_ms = sum(float(trace.get("latency_ms", 0)) for trace in llm_traces)

    return AgentTrace(
        sample_id=payload["scenario_id"],
        raw_input=payload.get("raw_input"),
        privileged_input=payload.get("privileged_input", ""),
        quarantined_output=payload.get("quarantined_output"),
        tool_request=tool_request,
        policy_verdict=policy_verdict["status"],
        final_outcome=payload.get("final_user_outcome", ""),
        latency_ms=latency_ms,
        metadata={
            "mode": payload.get("mode"),
            "scenario_title": payload.get("scenario_title"),
            "run_backend": payload.get("run_backend"),
            "decision": decision,
            "policy_verdict": policy_verdict,
            "llm_traces": llm_traces,
        },
    )
