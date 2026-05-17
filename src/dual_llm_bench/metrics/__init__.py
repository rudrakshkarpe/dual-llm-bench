from dual_llm_bench.metrics.exposure import PrivilegedContextExposure
from dual_llm_bench.metrics.injection import InjectionResistance
from dual_llm_bench.metrics.performance import CostEfficiency, LatencyOverhead
from dual_llm_bench.metrics.tool_safety import ToolDecisionSafetyF1
from dual_llm_bench.metrics.utility import UtilityRetention
from dual_llm_bench.models import Metric


def performance_metrics(
    *,
    latency_baseline_ms: float = 5_000,
    cost_budget_usd: float = 0.01,
) -> list[Metric]:
    return [
        LatencyOverhead(baseline_ms=latency_baseline_ms),
        CostEfficiency(budget_usd=cost_budget_usd),
    ]


def built_in_metrics(
    *,
    include_performance: bool = False,
    latency_baseline_ms: float = 5_000,
    cost_budget_usd: float = 0.01,
) -> list[Metric]:
    metrics: list[Metric] = [
        InjectionResistance(),
        PrivilegedContextExposure(),
        ToolDecisionSafetyF1(),
        UtilityRetention(),
    ]
    if include_performance:
        metrics.extend(
            performance_metrics(
                latency_baseline_ms=latency_baseline_ms,
                cost_budget_usd=cost_budget_usd,
            )
        )
    return metrics


__all__ = [
    "CostEfficiency",
    "InjectionResistance",
    "LatencyOverhead",
    "Metric",
    "PrivilegedContextExposure",
    "ToolDecisionSafetyF1",
    "UtilityRetention",
    "built_in_metrics",
    "performance_metrics",
]
