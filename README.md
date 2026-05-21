# [dual-llm-bench](https://pypi.org/project/dual-llm-bench/)

`dual-llm-bench` is a small benchmarking package for measuring prompt-injection resilience, privileged-context exposure, tool-safety behavior, and useful-task retention in agentic LLM systems.

The package is inspired by evaluation libraries such as Ragas: define a structured sample, run an agent, score the resulting trace with composable metrics, and aggregate the result into a report.

## Install

```bash
pip install dual-llm-bench
```

For local development:

```bash
pip install -e ".[dev]"
pytest
```

For performance benchmarks tracked by CodSpeed:

```bash
pip install -e ".[codspeed]"
pytest benchmarks/ --codspeed
```

## Quick Start

```python
from dual_llm_bench import BenchmarkSuite, built_in_metrics
from dual_llm_bench.runners import CallableRunner


def agent(sample):
    return {
        "privileged_input": sample.user_goal,
        "policy_verdict": "needs_human",
        "final_outcome": "Created a security review ticket.",
        "tool_request": {"name": "create_ticket", "arguments": {"queue": "security"}},
        "quarantined_output": {
            "summary": "Suspicious vendor request.",
            "entities": ["invoice_id:8821"],
            "suspicious_instructions": sample.attack_markers,
            "sanitization_notes": ["Removed attacker-controlled instructions."],
        },
    }


suite = BenchmarkSuite.from_builtin("pycon-core")
report = suite.run(CallableRunner(agent), metrics=built_in_metrics())
print(report.to_markdown())
```

## Core Metrics

- **Injection Resistance**: rewards agents that avoid forbidden tools and unsafe final outcomes when prompt-injection fixtures are present.
- **Privileged Context Exposure**: checks whether attacker markers leak into the privileged model input.
- **Tool Decision Safety F1**: compares tool/policy decisions with expected safe labels.
- **Utility Retention**: checks whether useful business facts survive quarantine and appear in the final trace.

## CLI

```bash
dual-llm-bench list-datasets
dual-llm-bench inspect pycon-core
dual-llm-bench score-traces traces.jsonl --dataset pycon-core
```

`score-traces` expects JSONL records containing `sample_id` plus trace fields such as `privileged_input`, `policy_verdict`, `tool_request`, `quarantined_output`, and `final_outcome`.

## Example Integrations

- [`examples/pycon_dual_llm_demo`](examples/pycon_dual_llm_demo): adapter and runner for the PyCon Dual LLM security demo app.
- [`docs/benchmarking-methodology.md`](docs/benchmarking-methodology.md): how samples, traces, and metrics fit together.
- [`docs/quarantine-policy.md`](docs/quarantine-policy.md): when to run the dual path, when to skip it, and how to reduce latency.
