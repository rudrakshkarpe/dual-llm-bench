from __future__ import annotations

from collections.abc import Iterable

from dual_llm_bench import AgentTrace, BenchmarkSuite, ToolRequest, built_in_metrics
from dual_llm_bench.datasets import available_datasets
from dual_llm_bench.models import BenchmarkSample, Metric


def _trace_for(sample: BenchmarkSample) -> AgentTrace:
    facts = ", ".join(sample.expected_facts) or "No expected facts."
    tool_name = next(iter(sorted(sample.expected_decision.allowed_tools)), None)
    tool_request = ToolRequest(
        name=tool_name,
        arguments={"queue": "security-review"},
        rationale="Route suspicious or sensitive content for review.",
    ) if tool_name else None

    return AgentTrace(
        sample_id=sample.id,
        privileged_input=f"Sanitized task for {sample.id}. Business facts: {facts}",
        quarantined_output={
            "summary": facts,
            "suspicious_instructions": sample.attack_markers,
            "sanitization_notes": ["Removed attacker-controlled instructions."],
        },
        policy_verdict=sample.expected_decision.verdict,
        tool_request=tool_request,
        final_outcome=f"Handled {sample.id} using verified facts: {facts}",
    )


def _benchmark_payload() -> list[tuple[BenchmarkSuite, list[AgentTrace]]]:
    payload = []
    for dataset in available_datasets():
        suite = BenchmarkSuite.from_builtin(dataset)
        payload.append((suite, [_trace_for(sample) for sample in suite.samples]))
    return payload


PAYLOAD = _benchmark_payload()
METRICS = built_in_metrics()
REPORTS = [suite.score_traces(traces, metrics=METRICS) for suite, traces in PAYLOAD]


def _score_all_datasets(
    payload: Iterable[tuple[BenchmarkSuite, list[AgentTrace]]],
    metrics: list[Metric],
) -> float:
    reports = [suite.score_traces(traces, metrics=metrics) for suite, traces in payload]
    return sum(report.overall_score for report in reports)


def _render_reports() -> int:
    return sum(len(report.to_markdown()) for report in REPORTS)


def test_score_all_builtin_datasets(benchmark) -> None:
    score = benchmark(_score_all_datasets, PAYLOAD, METRICS)

    assert score >= 0


def test_render_builtin_dataset_reports(benchmark) -> None:
    report_length = benchmark(_render_reports)

    assert report_length > 0
