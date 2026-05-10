from __future__ import annotations

import pytest

from dual_llm_bench.datasets import available_datasets, load_builtin_dataset
from dual_llm_bench.models import AttackType, BenchmarkSuite

ALL_DATASETS = available_datasets()


@pytest.mark.parametrize("name", ALL_DATASETS)
def test_dataset_loads_successfully(name: str) -> None:
    samples = load_builtin_dataset(name)
    assert len(samples) > 0


@pytest.mark.parametrize("name", ALL_DATASETS)
def test_dataset_via_suite(name: str) -> None:
    suite = BenchmarkSuite.from_builtin(name)
    assert suite.name == name
    assert len(suite.samples) > 0


def test_all_sample_ids_unique_across_datasets() -> None:
    all_ids: list[str] = []
    for name in ALL_DATASETS:
        samples = load_builtin_dataset(name)
        all_ids.extend(s.id for s in samples)
    assert len(all_ids) == len(set(all_ids)), f"Duplicate IDs found: {[i for i in all_ids if all_ids.count(i) > 1]}"


def test_attack_samples_have_forbidden_tools() -> None:
    for name in ALL_DATASETS:
        for sample in load_builtin_dataset(name):
            if sample.attack_type != AttackType.BENIGN:
                assert sample.expected_decision.forbidden_tools, (
                    f"Attack sample {sample.id} in {name} must have forbidden_tools"
                )


def test_benign_samples_have_empty_markers() -> None:
    for name in ALL_DATASETS:
        for sample in load_builtin_dataset(name):
            if sample.attack_type == AttackType.BENIGN:
                assert sample.attack_markers == [], (
                    f"Benign sample {sample.id} in {name} must have empty attack_markers"
                )
                assert not sample.expected_decision.forbidden_tools, (
                    f"Benign sample {sample.id} in {name} must have empty forbidden_tools"
                )


def test_attack_samples_have_markers() -> None:
    for name in ALL_DATASETS:
        for sample in load_builtin_dataset(name):
            if sample.attack_type != AttackType.BENIGN:
                assert len(sample.attack_markers) > 0, (
                    f"Attack sample {sample.id} in {name} must have attack_markers"
                )


def test_total_sample_count() -> None:
    total = sum(len(load_builtin_dataset(name)) for name in ALL_DATASETS)
    assert total >= 55


def test_unknown_dataset_raises() -> None:
    with pytest.raises(ValueError, match="Unknown built-in dataset"):
        load_builtin_dataset("nonexistent")


def test_expected_dataset_count() -> None:
    assert len(ALL_DATASETS) == 6
