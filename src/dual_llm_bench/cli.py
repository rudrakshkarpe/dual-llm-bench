from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

import typer

from dual_llm_bench.datasets import available_datasets
from dual_llm_bench.metrics import built_in_metrics
from dual_llm_bench.models import BenchmarkSuite
from dual_llm_bench.report import write_report
from dual_llm_bench.runners import load_jsonl_traces

app = typer.Typer(
    help="Benchmark prompt-injection resilience and tool safety for LLM agents.",
    no_args_is_help=True,
)


@app.command()
def list_datasets() -> None:
    """List packaged benchmark datasets."""
    for dataset in available_datasets():
        typer.echo(dataset)


@app.command()
def inspect(dataset: str = "pycon-core") -> None:
    """Print the samples included in a dataset."""
    suite = BenchmarkSuite.from_builtin(dataset)
    for sample in suite.samples:
        typer.echo(f"{sample.id}: {sample.title} [{sample.attack_type.value}]")


@app.command()
def score_traces(
    traces: Annotated[Path, typer.Argument(help="JSONL file containing AgentTrace records.")],
    dataset: Annotated[str, typer.Option(help="Built-in dataset name.")] = "pycon-core",
    output: Annotated[Path | None, typer.Option(help="Optional .md or .json report path.")] = None,
) -> None:
    """Score exported agent traces against a packaged dataset."""
    suite = BenchmarkSuite.from_builtin(dataset)
    report = suite.score_traces(load_jsonl_traces(traces), metrics=built_in_metrics())
    typer.echo(report.to_markdown())
    if output is not None:
        write_report(report, output)
        typer.echo(f"\nWrote report to {output}")


@app.command()
def baseline(
    traces: Annotated[Path, typer.Argument(help="JSONL file containing AgentTrace records.")],
    dataset: Annotated[str, typer.Option(help="Built-in dataset name.")] = "pycon-core",
    output: Annotated[Path, typer.Option(help="Baseline JSON output path.")] = Path(
        ".dlb-baseline.json"
    ),
) -> None:
    """Save current benchmark results as a baseline for CI regression checks."""
    suite = BenchmarkSuite.from_builtin(dataset)
    report = suite.score_traces(load_jsonl_traces(traces), metrics=built_in_metrics())
    payload = {
        "dataset": report.dataset_name,
        "trace_count": report.trace_count,
        "overall_score": report.overall_score,
        "metric_scores": report.metric_scores(),
    }
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    typer.echo(f"Baseline saved to {output} (overall: {report.overall_score:.3f})")


@app.command()
def ci(
    traces: Annotated[Path, typer.Argument(help="JSONL file containing AgentTrace records.")],
    dataset: Annotated[str, typer.Option(help="Built-in dataset name.")] = "pycon-core",
    baseline_path: Annotated[Path, typer.Option("--baseline", help="Baseline JSON path.")] = Path(
        ".dlb-baseline.json"
    ),
    threshold: Annotated[
        float, typer.Option(help="Max allowed regression per metric (0.0-1.0).")
    ] = 0.05,
) -> None:
    """Compare current traces against a baseline and fail on regression."""
    if not baseline_path.exists():
        typer.echo(f"Baseline file not found: {baseline_path}")
        typer.echo("Run 'dual-llm-bench baseline <traces>' first to create one.")
        raise typer.Exit(code=1)

    baseline_data = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline_metrics: dict[str, float] = baseline_data["metric_scores"]

    suite = BenchmarkSuite.from_builtin(dataset)
    report = suite.score_traces(load_jsonl_traces(traces), metrics=built_in_metrics())
    current_metrics = report.metric_scores()

    regressions: list[str] = []
    typer.echo("Metric                        Baseline  Current   Delta")
    typer.echo("-" * 58)
    for name in sorted(set(baseline_metrics) | set(current_metrics)):
        base_val = baseline_metrics.get(name, 0.0)
        curr_val = current_metrics.get(name, 0.0)
        delta = curr_val - base_val
        marker = ""
        if delta < -threshold:
            marker = " REGRESSION"
            regressions.append(
                f"{name}: {base_val:.3f} -> {curr_val:.3f} (delta: {delta:+.3f})"
            )
        typer.echo(f"{name:<30}{base_val:.3f}     {curr_val:.3f}     {delta:+.3f}{marker}")

    overall_delta = report.overall_score - baseline_data["overall_score"]
    typer.echo(f"\nOverall: {baseline_data['overall_score']:.3f} -> {report.overall_score:.3f} "
               f"(delta: {overall_delta:+.3f})")

    if regressions:
        typer.echo(f"\nFAILED: {len(regressions)} metric(s) regressed beyond {threshold} threshold:")
        for reg in regressions:
            typer.echo(f"  - {reg}")
        sys.exit(1)
    else:
        typer.echo(f"\nPASSED: No metric regressed beyond {threshold} threshold.")


if __name__ == "__main__":
    app()
