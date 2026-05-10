from __future__ import annotations

import json
import re
from collections.abc import Iterable
from typing import Any


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()


def flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(f"{key} {flatten_text(inner)}" for key, inner in value.items())
    if isinstance(value, list | tuple | set):
        return " ".join(flatten_text(item) for item in value)
    return json.dumps(value, sort_keys=True, default=str)


def contains_any(text: str, needles: Iterable[str]) -> list[str]:
    normalized = normalize_text(text)
    return [needle for needle in needles if normalize_text(needle) and normalize_text(needle) in normalized]


def token_set(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_:/.-]+", normalize_text(text)))


class SemanticMatcher:
    """Embedding-based similarity matcher with substring fallback.

    Requires ``sentence-transformers`` (install via ``pip install dual-llm-bench[semantic]``).
    When the library is unavailable, all methods fall back to exact substring matching.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        similarity_threshold: float = 0.65,
    ) -> None:
        self.similarity_threshold = similarity_threshold
        self._model: Any = None
        self._available: bool | None = None
        self._model_name = model_name

    @property
    def available(self) -> bool:
        if self._available is None:
            try:
                import sentence_transformers as _st  # type: ignore[import-not-found]

                self._model = _st.SentenceTransformer(self._model_name)
                self._available = True
            except ImportError:
                self._available = False
        return self._available

    def _cosine_similarity(self, a: Any, b: Any) -> float:
        dot = float(sum(x * y for x, y in zip(a, b, strict=False)))
        norm_a = float(sum(x * x for x in a)) ** 0.5
        norm_b = float(sum(x * x for x in b)) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    def similarity(self, text_a: str, text_b: str) -> float:
        if not self.available:
            norm_a = normalize_text(text_a)
            norm_b = normalize_text(text_b)
            if norm_a and norm_b and (norm_a in norm_b or norm_b in norm_a):
                return 1.0
            return 0.0
        embeddings = self._model.encode([text_a, text_b])
        return float(self._cosine_similarity(embeddings[0], embeddings[1]))

    def contains_any(
        self,
        text: str,
        needles: Iterable[str],
        threshold: float | None = None,
    ) -> list[str]:
        exact = contains_any(text, needles)
        if not self.available:
            return exact

        thresh = threshold if threshold is not None else self.similarity_threshold
        exact_set = set(exact)
        result = list(exact)

        remaining = [n for n in needles if n not in exact_set and normalize_text(n)]
        if not remaining:
            return result

        sentences = _split_sentences(text)
        if not sentences:
            return result

        needle_embeddings = self._model.encode(remaining)
        sentence_embeddings = self._model.encode(sentences)

        for i, needle in enumerate(remaining):
            for j in range(len(sentences)):
                score = float(self._cosine_similarity(
                    needle_embeddings[i], sentence_embeddings[j]
                ))
                if score >= thresh:
                    result.append(needle)
                    break

        return result


_DEFAULT_MATCHER: SemanticMatcher | None = None


def get_semantic_matcher(
    similarity_threshold: float = 0.65,
) -> SemanticMatcher:
    global _DEFAULT_MATCHER
    if _DEFAULT_MATCHER is None or _DEFAULT_MATCHER.similarity_threshold != similarity_threshold:
        _DEFAULT_MATCHER = SemanticMatcher(similarity_threshold=similarity_threshold)
    return _DEFAULT_MATCHER


def semantic_contains_any(
    text: str,
    needles: Iterable[str],
    similarity_threshold: float = 0.65,
) -> list[str]:
    matcher = get_semantic_matcher(similarity_threshold)
    return matcher.contains_any(text, needles)


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?;])\s+", text)
    return [p.strip() for p in parts if p.strip()]
