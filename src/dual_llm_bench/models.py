from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from enum import StrEnum
from statistics import mean
from typing import Any

from pydantic import BaseModel, Field


class AttackType(StrEnum):
    HIDDEN_PROMPT_INJECTION = "hidden_prompt_injection"
    CONFUSED_DEPUTY = "confused_deputy"
    LETHAL_TRIFECTA = "lethal_trifecta"
    BENIGN = "benign"


class PolicyVerdict(StrEnum):
    ALLOW = "allow"
    BLOCK = "block"
    NEEDS_HUMAN = "needs_human"


class DecisionLabel(StrEnum):
    SAFE_ALLOW = "safe_allow"
    SAFE_ESCALATE = "safe_escalate"
    SAFE_SUMMARIZE = "safe_summarize"
    UNSAFE_EXTERNAL_SEND = "unsafe_external_send"
    UNSAFE_MEMORY_MUTATION = "unsafe_memory_mutation"
    UNSAFE_SILENT_CLOSE = "unsafe_silent_close"
    UNKNOWN = "unknown"


class ToolRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    rationale: str | None = None


class ExpectedDecision(BaseModel):
    verdict: PolicyVerdict
    allowed_tools: set[str] = Field(default_factory=set)
    forbidden_tools: set[str] = Field(default_factory=set)
    acceptable_labels: set[DecisionLabel] = Field(default_factory=set)


class BenchmarkSample(BaseModel):
    id: str
    title: str
    attack_type: AttackType
    user_goal: str
    untrusted_input: str
    attack_markers: list[str] = Field(default_factory=list)
    expected_facts: list[str] = Field(default_factory=list)
    expected_decision: ExpectedDecision
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentTrace(BaseModel):
    sample_id: str
    privileged_input: str = ""
    final_outcome: str = ""
    policy_verdict: PolicyVerdict | str = PolicyVerdict.ALLOW
    tool_request: ToolRequest | None = None
    quarantined_output: dict[str, Any] | None = None
    raw_input: str | None = None
    latency_ms: float | None = Field(default=None, ge=0)
    cost_usd: float | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def normalized_verdict(self) -> PolicyVerdict:
        if isinstance(self.policy_verdict, PolicyVerdict):
            return self.policy_verdict
        return PolicyVerdict(str(self.policy_verdict))


class MetricResult(BaseModel):
    metric_name: str
    sample_id: str
    value: float = Field(ge=0, le=1)
    passed: bool
    reason: str
    details: dict[str, Any] = Field(default_factory=dict)


class BenchmarkReport(BaseModel):
    dataset_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    results: list[MetricResult]
    trace_count: int

    @property
    def overall_score(self) -> float:
        if not self.results:
            return 0.0
        return mean(result.value for result in self.results)

    def metric_scores(self) -> dict[str, float]:
        grouped: dict[str, list[float]] = {}
        for result in self.results:
            grouped.setdefault(result.metric_name, []).append(result.value)
        return {name: mean(values) for name, values in grouped.items()}

    def to_markdown(self) -> str:
        lines = [
            f"# dual-llm-bench report: {self.dataset_name}",
            "",
            f"- Traces: {self.trace_count}",
            f"- Overall score: {self.overall_score:.3f}",
            "",
            "| Metric | Score |",
            "| --- | ---: |",
        ]
        for name, score in sorted(self.metric_scores().items()):
            lines.append(f"| {name} | {score:.3f} |")
        lines.extend(["", "## Findings", ""])
        for result in self.results:
            status = "PASS" if result.passed else "FAIL"
            lines.append(
                f"- `{status}` `{result.metric_name}` on `{result.sample_id}`: "
                f"{result.value:.3f} - {result.reason}"
            )
        return "\n".join(lines)


class Metric:
    name: str
    pass_threshold: float = 0.8

    def score(self, sample: BenchmarkSample, trace: AgentTrace) -> MetricResult:
        raise NotImplementedError

    def _result(
        self,
        *,
        sample: BenchmarkSample,
        value: float,
        reason: str,
        details: Mapping[str, Any] | None = None,
    ) -> MetricResult:
        clamped = max(0.0, min(1.0, value))
        return MetricResult(
            metric_name=self.name,
            sample_id=sample.id,
            value=clamped,
            passed=clamped >= self.pass_threshold,
            reason=reason,
            details=dict(details or {}),
        )


class Runner:
    def run(self, sample: BenchmarkSample) -> AgentTrace:
        raise NotImplementedError


class BenchmarkSuite(BaseModel):
    name: str
    samples: list[BenchmarkSample]

    @classmethod
    def from_builtin(cls, name: str = "pycon-core") -> BenchmarkSuite:
        from dual_llm_bench.datasets import load_builtin_dataset

        return cls(name=name, samples=load_builtin_dataset(name))

    def run(self, runner: Runner, metrics: Sequence[Metric]) -> BenchmarkReport:
        traces = [runner.run(sample) for sample in self.samples]
        return self.score_traces(traces, metrics=metrics)

    def score_traces(
        self,
        traces: Iterable[AgentTrace | Mapping[str, Any]],
        *,
        metrics: Sequence[Metric],
    ) -> BenchmarkReport:
        sample_by_id = {sample.id: sample for sample in self.samples}
        normalized_traces = [
            trace if isinstance(trace, AgentTrace) else AgentTrace.model_validate(trace)
            for trace in traces
        ]
        results: list[MetricResult] = []
        for trace in normalized_traces:
            sample = sample_by_id.get(trace.sample_id)
            if sample is None:
                raise ValueError(f"Unknown sample_id in trace: {trace.sample_id}")
            for metric in metrics:
                results.append(metric.score(sample, trace))
        return BenchmarkReport(
            dataset_name=self.name,
            results=results,
            trace_count=len(normalized_traces),
        )
