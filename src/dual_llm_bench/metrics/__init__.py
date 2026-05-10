from dual_llm_bench.metrics.exposure import PrivilegedContextExposure
from dual_llm_bench.metrics.injection import InjectionResistance
from dual_llm_bench.metrics.tool_safety import ToolDecisionSafetyF1
from dual_llm_bench.metrics.utility import UtilityRetention
from dual_llm_bench.models import Metric


def built_in_metrics() -> list[Metric]:
    return [
        InjectionResistance(),
        PrivilegedContextExposure(),
        ToolDecisionSafetyF1(),
        UtilityRetention(),
    ]


__all__ = [
    "InjectionResistance",
    "Metric",
    "PrivilegedContextExposure",
    "ToolDecisionSafetyF1",
    "UtilityRetention",
    "built_in_metrics",
]
