from __future__ import annotations

import json
from importlib.resources import files

from dual_llm_bench.models import BenchmarkSample

_BUILTIN_DATASETS: dict[str, str] = {
    "pycon-core": "pycon_core.json",
    "encoding-attacks": "encoding_attacks.json",
    "false-positives": "false_positives.json",
    "tool-abuse": "tool_abuse.json",
    "authority-escalation": "authority_escalation.json",
    "data-exfiltration": "data_exfiltration.json",
}


def available_datasets() -> list[str]:
    return list(_BUILTIN_DATASETS.keys())


def load_builtin_dataset(name: str = "pycon-core") -> list[BenchmarkSample]:
    filename = _BUILTIN_DATASETS.get(name)
    if filename is None:
        raise ValueError(f"Unknown built-in dataset: {name}")
    payload = files("dual_llm_bench.datasets").joinpath(filename).read_text()
    return [BenchmarkSample.model_validate(item) for item in json.loads(payload)]
