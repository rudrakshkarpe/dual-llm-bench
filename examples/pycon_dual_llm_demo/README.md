# PyCon Dual LLM Demo Integration

This example shows how to benchmark the PyCon Dual LLM security demo app with `dual-llm-bench`.

The demo app owns the real application behavior:

- scenario fixtures
- baseline vs dual execution
- LLM calls
- policy gates
- tool request simulation
- application `RunTrace`

`dual-llm-bench` owns the evaluation:

- converts app traces into `AgentTrace`
- scores each sample
- writes JSON, Markdown, and JSONL reports

## Layout

```text
examples/pycon_dual_llm_demo/
  adapter.py
  run_demo_benchmark.py
  configs/
    local_ollama.json
    openrouter_claude.json
```

## Run Against the Demo App

Set `DEMO_REPO_PATH` to the PyCon demo repository:

```bash
export DEMO_REPO_PATH=/path/to/Securing-AI-agents-using-Dual-LLM-PyCon-US-26
python examples/pycon_dual_llm_demo/run_demo_benchmark.py \
  --config examples/pycon_dual_llm_demo/configs/local_ollama.json
```

For OpenRouter:

```bash
export OPENROUTER_API_KEY="..."
export DEMO_REPO_PATH=/path/to/Securing-AI-agents-using-Dual-LLM-PyCon-US-26
python examples/pycon_dual_llm_demo/run_demo_benchmark.py \
  --config examples/pycon_dual_llm_demo/configs/openrouter_claude.json
```

## What This Example Demonstrates

The example formalizes the benchmark boundary:

```text
Application code produces traces.
Benchmark package scores traces.
```

This keeps the package reusable. Any agent framework can use `dual-llm-bench` if it can export the same trace fields.

## Best-Practice Hooks

The demo should add these production-oriented controls:

- selective quarantine based on source trust and tool risk
- content-hash caching for reviewer outputs
- shorter reviewer schemas for lower latency
- explicit business fact preservation to avoid utility loss
- risk labels instead of raw attacker instructions in privileged prompts
- fail-closed policy when reviewer confidence is low
