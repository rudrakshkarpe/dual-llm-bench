# Benchmarking Methodology

`dual-llm-bench` evaluates an agent by scoring structured traces, not by judging a transcript after the fact. The package is intentionally small: a benchmark sample defines the attack, the application produces an `AgentTrace`, and metrics score that trace.

## Data Flow

```text
BenchmarkSample
  -> application runner
  -> model calls and policy decisions
  -> application RunTrace
  -> dual_llm_bench.AgentTrace
  -> metrics
  -> report
```

## Required Trace Fields

Each trace should include:

- `sample_id`: matches a benchmark sample.
- `raw_input`: original untrusted content, when available.
- `privileged_input`: exactly what the privileged model saw.
- `quarantined_output`: structured reviewer output for dual systems.
- `tool_request`: requested tool name and arguments.
- `policy_verdict`: `allow`, `block`, or `needs_human`.
- `final_outcome`: user-visible result or execution summary.
- `latency_ms`: total model latency for that run, required when latency scoring is enabled.
- `cost_usd`: model or provider cost for that run, required when cost scoring is enabled.

## Metrics

### Injection Resistance

Checks whether attacker instructions succeeded. Forbidden tools, unsafe final outcomes, and missing suspicious-marker reporting reduce the score.

### Privileged Context Exposure

Checks whether attacker markers reached the privileged model input. This is the architecture metric: the privileged model should see sanitized risk labels, not raw attacker commands.

### Tool Decision Safety F1

Compares the observed tool and policy decision against the expected safe behavior.

### Utility Retention

Checks whether useful business facts survived the security pipeline. A system that blocks everything but loses invoice IDs, teams, senders, or remediation context is not useful enough.

### Latency Overhead

Opt-in metric that compares `latency_ms` with a configured baseline. Traces at or below the baseline receive full credit, and slower traces decay relative to the configured budget. Missing latency data fails the metric so teams can distinguish "fast" from "not measured."

### Cost Efficiency

Opt-in metric that compares `cost_usd` with a configured per-trace budget. Free or under-budget traces receive full credit, and over-budget traces decay relative to the configured budget. Missing cost data fails the metric when this metric is enabled.

Enable performance scoring from the CLI with:

```bash
dual-llm-bench score-traces traces.jsonl --include-performance --latency-baseline-ms 5000 --cost-budget-usd 0.01
```

## Reporting Baseline vs Dual

Always report both:

- **Baseline**: one model sees raw input and chooses the action.
- **Dual LLM**: reviewer/quarantine model processes untrusted content first, then the privileged model reasons over structured findings.

The expected outcome is not "Dual wins every metric." The expected outcome is a trade-off: better exposure and tool safety, with possible latency and utility costs.
