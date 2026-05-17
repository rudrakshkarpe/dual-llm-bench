from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dual_llm_bench.models import BenchmarkReport


def _report_payload(report: BenchmarkReport) -> dict[str, Any]:
    return {
        "summary": {
            "dataset": report.dataset_name,
            "trace_count": report.trace_count,
            "overall_score": report.overall_score,
            "metric_scores": report.metric_scores(),
        },
        "results": [result.model_dump() for result in report.results],
    }


def write_report(report: BenchmarkReport, path: str | Path) -> None:
    destination = Path(path)
    if destination.suffix == ".json":
        destination.write_text(json.dumps(_report_payload(report), indent=2), encoding="utf-8")
        return
    if destination.suffix in {".md", ".markdown"}:
        destination.write_text(report.to_markdown(), encoding="utf-8")
        return
    destination.write_text(json.dumps(_report_payload(report), indent=2), encoding="utf-8")
