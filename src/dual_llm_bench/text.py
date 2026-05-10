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
