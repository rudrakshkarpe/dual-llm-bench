from __future__ import annotations

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
    suite = BenchmarkSuite.from_builtin(dataset)  # type: ignore[arg-type]
    for sample in suite.samples:
        typer.echo(f"{sample.id}: {sample.title} [{sample.attack_type.value}]")


@app.command()
def score_traces(
    traces: Annotated[Path, typer.Argument(help="JSONL file containing AgentTrace records.")],
    dataset: Annotated[str, typer.Option(help="Built-in dataset name.")] = "pycon-core",
    output: Annotated[Path | None, typer.Option(help="Optional .md or .json report path.")] = None,
) -> None:
    """Score exported agent traces against a packaged dataset."""
    suite = BenchmarkSuite.from_builtin(dataset)  # type: ignore[arg-type]
    report = suite.score_traces(load_jsonl_traces(traces), metrics=built_in_metrics())
    typer.echo(report.to_markdown())
    if output is not None:
        write_report(report, output)
        typer.echo(f"\nWrote report to {output}")


if __name__ == "__main__":
    app()
