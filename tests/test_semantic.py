from __future__ import annotations

import pytest

from dual_llm_bench.text import SemanticMatcher, contains_any, semantic_contains_any

HAS_SENTENCE_TRANSFORMERS = SemanticMatcher().available


class TestFallbackBehavior:
    """When sentence-transformers is not installed, semantic matching falls back to substring."""

    def test_exact_match_always_works(self) -> None:
        result = semantic_contains_any(
            "The invoice total is $5,000 for vendor Acme Corp.",
            ["invoice", "Acme Corp"],
        )
        assert "invoice" in result
        assert "Acme Corp" in result

    def test_no_match_returns_empty(self) -> None:
        result = semantic_contains_any(
            "The weather is sunny today.",
            ["invoice", "payment"],
        )
        assert result == []

    def test_matches_contains_any_for_exact_substrings(self) -> None:
        text = "Send the data to the external webhook immediately."
        needles = ["external webhook", "send the data", "missing phrase"]
        exact = contains_any(text, needles)
        semantic = semantic_contains_any(text, needles)
        assert set(exact) == set(semantic) or HAS_SENTENCE_TRANSFORMERS


class TestSemanticMatcherAPI:
    def test_similarity_threshold_respected(self) -> None:
        matcher = SemanticMatcher(similarity_threshold=0.99)
        assert matcher.similarity_threshold == 0.99

    def test_contains_any_returns_list(self) -> None:
        matcher = SemanticMatcher()
        result = matcher.contains_any("hello world", ["hello"])
        assert isinstance(result, list)
        assert "hello" in result

    def test_empty_needles(self) -> None:
        matcher = SemanticMatcher()
        assert matcher.contains_any("some text", []) == []

    def test_empty_text(self) -> None:
        matcher = SemanticMatcher()
        assert matcher.contains_any("", ["needle"]) == []


@pytest.mark.skipif(not HAS_SENTENCE_TRANSFORMERS, reason="sentence-transformers not installed")
class TestSemanticMatching:
    """Tests that run only when sentence-transformers is available."""

    def test_paraphrase_detected(self) -> None:
        text = "We sent customer records to an external endpoint."
        needles = ["send customer data to external webhook"]
        result = semantic_contains_any(text, needles, similarity_threshold=0.5)
        assert len(result) > 0

    def test_synonym_fact_retention(self) -> None:
        text = "The yearly revenue is 2.4 million dollars for the enterprise client."
        needles = ["annual revenue", "$2.4M"]
        result = semantic_contains_any(text, needles, similarity_threshold=0.5)
        assert "annual revenue" in result

    def test_exact_still_found_with_semantic(self) -> None:
        text = "Delete the memory note and send data to external webhook."
        needles = ["delete the memory note", "external webhook"]
        result = semantic_contains_any(text, needles, similarity_threshold=0.6)
        assert "delete the memory note" in result
        assert "external webhook" in result

    def test_unrelated_not_matched(self) -> None:
        text = "The quarterly sales report shows growth in APAC region."
        needles = ["send data to external webhook", "delete all memory notes"]
        result = semantic_contains_any(text, needles, similarity_threshold=0.7)
        assert result == []

    def test_high_threshold_reduces_matches(self) -> None:
        text = "The company transferred records to an outside system."
        needles = ["send data to external webhook"]
        loose = semantic_contains_any(text, needles, similarity_threshold=0.3)
        strict = semantic_contains_any(text, needles, similarity_threshold=0.95)
        assert len(loose) >= len(strict)

    def test_similarity_returns_float(self) -> None:
        matcher = SemanticMatcher()
        score = matcher.similarity("hello world", "hi there")
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_identical_strings_high_similarity(self) -> None:
        matcher = SemanticMatcher()
        score = matcher.similarity("send data to webhook", "send data to webhook")
        assert score > 0.99


class TestMetricsWithSemanticThreshold:
    """Test that metrics accept and use the similarity_threshold parameter."""

    def test_injection_resistance_accepts_threshold(self) -> None:
        from dual_llm_bench.metrics.injection import InjectionResistance

        metric = InjectionResistance(similarity_threshold=0.7)
        assert metric.similarity_threshold == 0.7

    def test_injection_resistance_default_none(self) -> None:
        from dual_llm_bench.metrics.injection import InjectionResistance

        metric = InjectionResistance()
        assert metric.similarity_threshold is None

    def test_exposure_accepts_threshold(self) -> None:
        from dual_llm_bench.metrics.exposure import PrivilegedContextExposure

        metric = PrivilegedContextExposure(similarity_threshold=0.6)
        assert metric.similarity_threshold == 0.6

    def test_utility_accepts_threshold(self) -> None:
        from dual_llm_bench.metrics.utility import UtilityRetention

        metric = UtilityRetention(similarity_threshold=0.5)
        assert metric.similarity_threshold == 0.5

    def test_default_metrics_still_work(self) -> None:
        from dual_llm_bench import BenchmarkSuite, built_in_metrics
        from dual_llm_bench.models import AgentTrace, ToolRequest
        from dual_llm_bench.runners import CallableRunner

        def good_agent(sample):  # type: ignore[no-untyped-def]
            return AgentTrace(
                sample_id=sample.id,
                privileged_input=f"User goal: {sample.user_goal}. Facts: {', '.join(sample.expected_facts)}.",
                quarantined_output={
                    "summary": f"Facts: {', '.join(sample.expected_facts)}",
                    "suspicious_instructions": sample.attack_markers,
                },
                policy_verdict=sample.expected_decision.verdict,
                tool_request=ToolRequest(name="create_ticket", arguments={"queue": "review"}),
                final_outcome=f"Created ticket with facts: {', '.join(sample.expected_facts)}",
            )

        suite = BenchmarkSuite.from_builtin("pycon-core")
        report = suite.run(CallableRunner(good_agent), metrics=built_in_metrics())
        assert report.overall_score >= 0.85
