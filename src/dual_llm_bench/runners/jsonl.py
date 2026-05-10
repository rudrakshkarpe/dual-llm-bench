from __future__ import annotations

import json
from pathlib import Path

from dual_llm_bench.models import AgentTrace


def load_jsonl_traces(path: str | Path) -> list[AgentTrace]:
    traces: list[AgentTrace] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                traces.append(AgentTrace.model_validate(json.loads(stripped)))
            except Exception as exc:
                raise ValueError(f"Invalid trace JSONL at line {line_number}: {exc}") from exc
    return traces
