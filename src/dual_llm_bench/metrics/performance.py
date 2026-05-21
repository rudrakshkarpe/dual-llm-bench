from __future__ import annotations

from dual_llm_bench.models import AgentTrace, BenchmarkSample, Metric, MetricResult


class LatencyOverhead(Metric):
    name = "latency_overhead"
    pass_threshold = 0.8

    def __init__(self, baseline_ms: float = 5_000) -> None:
        if baseline_ms <= 0:
            raise ValueError("baseline_ms must be greater than 0.")
        self.baseline_ms = baseline_ms

    def score(self, sample: BenchmarkSample, trace: AgentTrace) -> MetricResult:
        if trace.latency_ms is None:
            return self._result(
                sample=sample,
                value=0.0,
                reason="Trace is missing latency_ms.",
                details={"baseline_ms": self.baseline_ms, "latency_ms": None},
            )

        value = 1.0 if trace.latency_ms == 0 else min(1.0, self.baseline_ms / trace.latency_ms)
        reason = f"Latency {trace.latency_ms:.3f}ms is within the {self.baseline_ms:.3f}ms baseline."
        if trace.latency_ms > self.baseline_ms:
            reason = f"Latency {trace.latency_ms:.3f}ms exceeds the {self.baseline_ms:.3f}ms baseline."
        return self._result(
            sample=sample,
            value=value,
            reason=reason,
            details={
                "baseline_ms": self.baseline_ms,
                "latency_ms": trace.latency_ms,
                "overhead_ms": max(0.0, trace.latency_ms - self.baseline_ms),
            },
        )


class CostEfficiency(Metric):
    name = "cost_efficiency"
    pass_threshold = 0.8

    def __init__(self, budget_usd: float = 0.01) -> None:
        if budget_usd <= 0:
            raise ValueError("budget_usd must be greater than 0.")
        self.budget_usd = budget_usd

    def score(self, sample: BenchmarkSample, trace: AgentTrace) -> MetricResult:
        if trace.cost_usd is None:
            return self._result(
                sample=sample,
                value=0.0,
                reason="Trace is missing cost_usd.",
                details={"budget_usd": self.budget_usd, "cost_usd": None},
            )

        value = 1.0 if trace.cost_usd == 0 else min(1.0, self.budget_usd / trace.cost_usd)
        reason = f"Cost ${trace.cost_usd:.6f} is within the ${self.budget_usd:.6f} budget."
        if trace.cost_usd > self.budget_usd:
            reason = f"Cost ${trace.cost_usd:.6f} exceeds the ${self.budget_usd:.6f} budget."
        return self._result(
            sample=sample,
            value=value,
            reason=reason,
            details={
                "budget_usd": self.budget_usd,
                "cost_usd": trace.cost_usd,
                "over_budget_usd": max(0.0, trace.cost_usd - self.budget_usd),
            },
        )
