from __future__ import annotations

import json

from dual_llm_bench.metrics import built_in_metrics
from dual_llm_bench.models import AgentTrace, BenchmarkSuite
from dual_llm_bench.report import write_report


def test_performance_metrics_are_reported_in_markdown_and_json(tmp_path) -> None:
    suite = BenchmarkSuite.from_builtin("pycon-core")
    sample = suite.samples[0]
    report = suite.score_traces(
        [
            AgentTrace(
                sample_id=sample.id,
                privileged_input="Sanitized facts: invoice 8821 ACH finance.",
                quarantined_output={
                    "summary": "invoice 8821 ACH finance",
                    "suspicious_instructions": sample.attack_markers,
                },
                policy_verdict=sample.expected_decision.verdict,
                final_outcome="Created finance ticket for invoice 8821 ACH verification.",
                latency_ms=750,
                cost_usd=0.003,
            )
        ],
        metrics=built_in_metrics(
            include_performance=True,
            latency_baseline_ms=1_000,
            cost_budget_usd=0.01,
        ),
    )

    markdown = report.to_markdown()
    assert "latency_overhead" in markdown
    assert "cost_efficiency" in markdown

    output = tmp_path / "report.json"
    write_report(report, output)

    payload = json.loads(output.read_text())
    assert "latency_overhead" in payload["summary"]["metric_scores"]
    assert "cost_efficiency" in payload["summary"]["metric_scores"]
