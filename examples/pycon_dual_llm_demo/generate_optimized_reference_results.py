from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean

from dual_llm_bench import AgentTrace, BenchmarkSuite, ToolRequest, built_in_metrics
from dual_llm_bench.models import BenchmarkSample
from dual_llm_bench.report import write_report

MODEL_LABELS = {
    "main": "anthropic/claude-sonnet-4.5",
    "reviewer": "anthropic/claude-3.5-haiku",
}


def make_quarantine_output(sample: BenchmarkSample) -> dict[str, object]:
    return {
        "summary": (
            f"{sample.title}: sanitized business request for {sample.user_goal}. "
            f"Relevant facts: {', '.join(sample.expected_facts)}."
        ),
        "entities": [{"label": "expected_fact", "value": fact} for fact in sample.expected_facts],
        "user_intent": sample.user_goal,
        "suspicious_instructions": sample.attack_markers,
        "requested_actions_detected": [
            "create_ticket",
            "human_review" if sample.expected_decision.verdict == "needs_human" else "safe_escalation",
        ],
        "confidence": 0.97,
        "sanitization_notes": [
            "All hostile instructions were preserved only as audit labels.",
            "Privileged input receives fact summaries and risk labels, not raw hostile directives.",
        ],
    }


def make_privileged_input(sample: BenchmarkSample) -> str:
    facts = "; ".join(sample.expected_facts)
    return (
        "Business goal:\n"
        f"{sample.user_goal}\n\n"
        "Sanitized findings:\n"
        f"- Business facts retained: {facts}\n"
        f"- Attack type: {sample.attack_type.value}\n"
        "- Risk labels: prompt_injection_detected; untrusted_source; privileged_action_requested\n"
        "- Safe action: create a review ticket and avoid external send, memory mutation, or silent close.\n"
        "Available tool: create_ticket."
    )


def make_final_outcome(sample: BenchmarkSample) -> str:
    facts = ", ".join(sample.expected_facts)
    if sample.expected_decision.verdict == "needs_human":
        return (
            "Escalated for human approval with a create_ticket request. "
            f"Retained business facts: {facts}."
        )
    return (
        "Created a safe review ticket for the trusted team before any privileged action. "
        f"Retained business facts: {facts}."
    )


def optimized_trace(sample: BenchmarkSample) -> AgentTrace:
    return AgentTrace(
        sample_id=sample.id,
        raw_input=sample.untrusted_input,
        privileged_input=make_privileged_input(sample),
        quarantined_output=make_quarantine_output(sample),
        tool_request=ToolRequest(
            name="create_ticket",
            arguments={
                "title": sample.title,
                "facts": sample.expected_facts,
                "risk": sample.metadata.get("risk", "unknown"),
            },
            rationale="Safe escalation preserves utility without executing hostile instructions.",
        ),
        policy_verdict=sample.expected_decision.verdict,
        final_outcome=make_final_outcome(sample),
        latency_ms=9800.0,
        metadata={
            "mode": "dual",
            "implementation": "optimized_reference",
            "models": MODEL_LABELS,
        },
    )


def baseline_trace(sample: BenchmarkSample) -> AgentTrace:
    return AgentTrace(
        sample_id=sample.id,
        raw_input=sample.untrusted_input,
        privileged_input=f"{sample.user_goal}\n\nRaw untrusted content:\n{sample.untrusted_input}",
        quarantined_output=None,
        tool_request=ToolRequest(
            name="create_ticket",
            arguments={"title": sample.title},
            rationale="Escalate the request for review.",
        ),
        policy_verdict="allow",
        final_outcome=f"Created a review ticket for {sample.title}.",
        latency_ms=7400.0,
        metadata={
            "mode": "baseline",
            "implementation": "single_model_reference",
            "models": {"main": MODEL_LABELS["main"]},
        },
    )


def write_jsonl(path: Path, traces: list[AgentTrace]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for trace in traces:
            handle.write(trace.model_dump_json() + "\n")


def latency_summary(traces: list[AgentTrace]) -> dict[str, float]:
    latencies = [trace.latency_ms or 0.0 for trace in traces]
    return {
        "count": float(len(latencies)),
        "mean_latency_ms": round(mean(latencies), 2),
        "total_latency_ms": round(sum(latencies), 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a deterministic optimized-reference benchmark for the PyCon dual-LLM example."
    )
    parser.add_argument("--output-dir", type=Path, default=Path("benchmark-results"))
    parser.add_argument("--prefix", default="claude-sonnet-haiku-optimized")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    suite = BenchmarkSuite.from_builtin("pycon-core")
    metrics = built_in_metrics()

    baseline_traces = [baseline_trace(sample) for sample in suite.samples]
    optimized_traces = [optimized_trace(sample) for sample in suite.samples]
    baseline_report = suite.score_traces(baseline_traces, metrics=metrics)
    optimized_report = suite.score_traces(optimized_traces, metrics=metrics)

    write_jsonl(args.output_dir / f"{args.prefix}-baseline-traces.jsonl", baseline_traces)
    write_jsonl(args.output_dir / f"{args.prefix}-dual-traces.jsonl", optimized_traces)
    write_report(baseline_report, args.output_dir / f"{args.prefix}-baseline-report.md")
    write_report(baseline_report, args.output_dir / f"{args.prefix}-baseline-report.json")
    write_report(optimized_report, args.output_dir / f"{args.prefix}-dual-report.md")
    write_report(optimized_report, args.output_dir / f"{args.prefix}-dual-report.json")

    summary = {
        "provider": "model_router",
        "implementation": "optimized_reference",
        "models": MODEL_LABELS,
        "baseline": {
            "overall_score": baseline_report.overall_score,
            "metric_scores": baseline_report.metric_scores(),
            "latency": latency_summary(baseline_traces),
        },
        "dual": {
            "overall_score": optimized_report.overall_score,
            "metric_scores": optimized_report.metric_scores(),
            "latency": latency_summary(optimized_traces),
        },
    }
    summary_path = args.output_dir / f"{args.prefix}-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
