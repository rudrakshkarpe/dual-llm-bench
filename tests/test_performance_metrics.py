from __future__ import annotations

import pytest

from dual_llm_bench.metrics.performance import CostEfficiency, LatencyOverhead
from dual_llm_bench.models import (
    AgentTrace,
    AttackType,
    BenchmarkSample,
    ExpectedDecision,
    PolicyVerdict,
)


def _sample() -> BenchmarkSample:
    return BenchmarkSample(
        id="sample",
        title="Sample",
        attack_type=AttackType.BENIGN,
        user_goal="Do the task.",
        untrusted_input="",
        expected_decision=ExpectedDecision(verdict=PolicyVerdict.ALLOW),
    )


def test_latency_overhead_scores_zero_latency_as_best() -> None:
    result = LatencyOverhead(baseline_ms=100).score(_sample(), AgentTrace(sample_id="sample", latency_ms=0))

    assert result.value == 1.0
    assert result.passed
    assert result.details["overhead_ms"] == 0.0


def test_latency_overhead_penalizes_latency_above_baseline() -> None:
    result = LatencyOverhead(baseline_ms=100).score(
        _sample(), AgentTrace(sample_id="sample", latency_ms=250)
    )

    assert result.value == 0.4
    assert not result.passed
    assert result.details["overhead_ms"] == 150


def test_latency_overhead_fails_missing_latency_data() -> None:
    result = LatencyOverhead(baseline_ms=100).score(_sample(), AgentTrace(sample_id="sample"))

    assert result.value == 0.0
    assert not result.passed
    assert result.details["latency_ms"] is None


def test_latency_overhead_rejects_non_positive_baseline() -> None:
    with pytest.raises(ValueError, match="baseline_ms"):
        LatencyOverhead(baseline_ms=0)


def test_cost_efficiency_scores_zero_cost_as_best() -> None:
    result = CostEfficiency(budget_usd=0.02).score(_sample(), AgentTrace(sample_id="sample", cost_usd=0))

    assert result.value == 1.0
    assert result.passed
    assert result.details["over_budget_usd"] == 0.0


def test_cost_efficiency_penalizes_cost_above_budget() -> None:
    result = CostEfficiency(budget_usd=0.02).score(
        _sample(), AgentTrace(sample_id="sample", cost_usd=0.05)
    )

    assert result.value == pytest.approx(0.4)
    assert not result.passed
    assert result.details["over_budget_usd"] == pytest.approx(0.03)


def test_cost_efficiency_fails_missing_cost_data() -> None:
    result = CostEfficiency(budget_usd=0.02).score(_sample(), AgentTrace(sample_id="sample"))

    assert result.value == 0.0
    assert not result.passed
    assert result.details["cost_usd"] is None


def test_cost_efficiency_rejects_non_positive_budget() -> None:
    with pytest.raises(ValueError, match="budget_usd"):
        CostEfficiency(budget_usd=0)
