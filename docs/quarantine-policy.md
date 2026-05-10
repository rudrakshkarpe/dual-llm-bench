# Quarantine Policy

Dual LLM systems should not run the slow path for every request. The goal is selective quarantine: use the reviewer model when data crosses a trust boundary or when a tool action could cause harm.

## Run Quarantine

Use the dual path when any of these are true:

| Signal | Examples | Why |
| --- | --- | --- |
| External content | Email, webpage, PDF, uploaded document, MCP resource | Content may contain hidden instructions. |
| Third-party authority claim | "The CFO approved this", "Legal requires this now" | Authority claims inside untrusted content are facts to verify, not commands. |
| State-changing tool | Email reply, ticket closure, memory mutation, webhook send | Tool impact increases the cost of prompt injection. |
| External destination | URL, webhook, storage bucket, partner endpoint | Attacker-supplied destinations are common exfiltration paths. |
| Sensitive domain | Finance, security, HR, customer data, compliance | Human review is often cheaper than a bad automation. |

## Skip Quarantine

Use the fast path when all of these are true:

| Signal | Examples | Guardrail |
| --- | --- | --- |
| Trusted source | Internal config, first-party service output | Preserve provenance. |
| Read-only action | Summarize already-trusted notes | No external send or mutation. |
| Low-risk tool | Local formatting, draft-only response | Do not execute writes automatically. |
| No authority transition | User directly asks for a harmless operation | Keep audit logs. |

## Latency Controls

The dual path adds latency because it performs at least two model calls. Reduce latency with:

- Content hashing and quarantine-result caching.
- Smaller reviewer model for extraction.
- Short schemas with required fields only.
- Strict `max_tokens`.
- Selective quarantine based on trust and tool risk.
- Async execution for independent samples.
- Fast fail-closed policy when reviewer confidence is low.

## Utility Controls

Over-sanitization can remove useful facts. Preserve utility by requiring the reviewer to emit:

- `business_facts`
- `entities`
- `source_provenance`
- `authority_claims`
- `requested_actions_detected`
- `suspicious_instruction_labels`
- `missing_context_risk`

Keep raw attacker wording out of privileged input, but keep short risk labels so reviewers and policy code know what happened.
