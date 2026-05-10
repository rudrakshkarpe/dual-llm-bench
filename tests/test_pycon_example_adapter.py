from __future__ import annotations

from examples.pycon_dual_llm_demo.adapter import trace_dict_to_agent_trace


def test_trace_dict_to_agent_trace_maps_demo_payload():
    trace = trace_dict_to_agent_trace(
        {
            "scenario_id": "hidden-prompt-injection",
            "mode": "dual",
            "scenario_title": "Hidden Prompt Injection",
            "run_backend": "test",
            "raw_input": "raw",
            "privileged_input": "sanitized",
            "quarantined_output": {"summary": "invoice 8821"},
            "decision": {
                "recommended_action": "Create ticket",
                "tool_request": {
                    "name": "create_ticket",
                    "arguments": {"queue": "finance"},
                    "rationale": "verification required",
                },
            },
            "policy_verdict": {"status": "allow"},
            "final_user_outcome": "Created ticket",
            "llm_traces": [{"latency_ms": 10.5}, {"latency_ms": 4.5}],
        }
    )

    assert trace.sample_id == "hidden-prompt-injection"
    assert trace.tool_request is not None
    assert trace.tool_request.name == "create_ticket"
    assert trace.latency_ms == 15.0
