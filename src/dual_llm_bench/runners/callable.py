from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from dual_llm_bench.models import AgentTrace, BenchmarkSample, Runner

AgentCallable = Callable[[BenchmarkSample], AgentTrace | Mapping[str, Any]]


class CallableRunner(Runner):
    def __init__(self, agent: AgentCallable) -> None:
        self.agent = agent

    def run(self, sample: BenchmarkSample) -> AgentTrace:
        result = self.agent(sample)
        if isinstance(result, AgentTrace):
            return result
        payload = dict(result)
        payload.setdefault("sample_id", sample.id)
        return AgentTrace.model_validate(payload)
