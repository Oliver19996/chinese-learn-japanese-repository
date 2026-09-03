from __future__ import annotations

import re
from difflib import SequenceMatcher

PUNCT_RE = re.compile(r"[\s\u3000、。！？!?？！,.「」『』（）()【】\[\]〜~・…]+")


def normalize(text: str) -> str:
    return PUNCT_RE.sub("", (text or "").strip())


def similarity(a: str, b: str) -> int:
    left, right = normalize(a), normalize(b)
    if not left and not right:
        return 100
    if not left or not right:
        return 0
    return int(round(SequenceMatcher(None, left, right).ratio() * 100))


def best_score(answer: str, correct_ja: str, correct_reading: str = "") -> int:
    scores = [similarity(answer, correct_ja)]
    if correct_reading:
        scores.append(similarity(answer, correct_reading))
        scores.append(similarity(normalize(answer), normalize(correct_reading)))
    return max(scores)


def comment_zh(score: int) -> str:
    if score >= 85:
        return "很好"
    if score >= 60:
        return "再试一次"
    return "注意助词"


def char_diff(answer: str, correct: str) -> list[dict[str, str]]:
    left = list(normalize(answer))
    right = list(normalize(correct))
    matcher = SequenceMatcher(None, left, right)
    tokens: list[dict[str, str]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for ch in right[j1:j2]:
                tokens.append({"t": ch, "kind": "match"})
        elif tag == "replace":
            for ch in left[i1:i2]:
                tokens.append({"t": ch, "kind": "wrong"})
            for ch in right[j1:j2]:
                tokens.append({"t": ch, "kind": "missing"})
        elif tag == "delete":
            for ch in left[i1:i2]:
                tokens.append({"t": ch, "kind": "wrong"})
        elif tag == "insert":
            for ch in right[j1:j2]:
                tokens.append({"t": ch, "kind": "missing"})
    return tokens
