from __future__ import annotations

import json
from functools import lru_cache

from app.config import SEED_DIR
from app.schemas import DictionaryItem
from app.services.llm import explain_word


@lru_cache(maxsize=1)
def _words() -> list[dict]:
    path = SEED_DIR / "seed_words.json"
    return json.loads(path.read_text(encoding="utf-8"))


def search_seed(query: str, limit: int = 8) -> list[DictionaryItem]:
    raw = (query or "").strip()
    q = raw.lower()
    if not q:
        return []
    hits: list[DictionaryItem] = []
    for row in _words():
        ja = str(row.get("ja", ""))
        reading = str(row.get("reading", ""))
        zh = str(row.get("zh", ""))
        blob = f"{ja}{reading}{zh}".lower()
        if q in blob or q in ja or q in reading or (zh and zh in q) or (ja and ja in q):
            hits.append(DictionaryItem.model_validate(row))
    hits.sort(key=lambda item: (item.ja != raw, item.zh != raw, len(item.ja)))
    return hits[:limit]


def lookup(query: str) -> list[DictionaryItem]:
    q = (query or "").strip()
    if not q:
        return []
    hits = search_seed(q)
    if hits:
        return hits
    item = explain_word(q)
    return [item] if item else []
