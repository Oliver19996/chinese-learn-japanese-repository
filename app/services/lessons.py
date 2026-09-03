from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from app.config import SEED_DIR


@lru_cache(maxsize=1)
def shadowing_lessons() -> list[dict[str, Any]]:
    return json.loads((SEED_DIR / "shadowing_lessons.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def dictation_lessons() -> list[dict[str, Any]]:
    return json.loads((SEED_DIR / "dictation_lessons.json").read_text(encoding="utf-8"))


def get_shadowing(lesson_id: str) -> dict[str, Any] | None:
    for lesson in shadowing_lessons():
        if lesson["id"] == lesson_id:
            return lesson
    return None


def get_dictation(lesson_id: str) -> dict[str, Any] | None:
    for lesson in dictation_lessons():
        if lesson["id"] == lesson_id:
            return lesson
    return None


def find_item(lesson: dict[str, Any], item_id: str) -> dict[str, Any] | None:
    for item in lesson.get("items", []):
        if item["id"] == item_id:
            return item
    return None


def lesson_summaries(lessons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for lesson in lessons:
        out.append(
            {
                "id": lesson["id"],
                "title_zh": lesson["title_zh"],
                "title_ja": lesson.get("title_ja", ""),
                "count": len(lesson.get("items", [])),
            }
        )
    return out
