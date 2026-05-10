from __future__ import annotations

import json
from importlib.resources import files
from typing import Literal

from dual_llm_bench.models import BenchmarkSample


def available_datasets() -> list[str]:
    return ["pycon-core"]


def load_builtin_dataset(name: Literal["pycon-core"] = "pycon-core") -> list[BenchmarkSample]:
    if name != "pycon-core":
        raise ValueError(f"Unknown built-in dataset: {name}")
    payload = files("dual_llm_bench.datasets").joinpath("pycon_core.json").read_text()
    return [BenchmarkSample.model_validate(item) for item in json.loads(payload)]
