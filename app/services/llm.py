from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.schemas import ConversationLLMOut, DictionaryItem, RubyToken
from app.services.openai_client import OpenAIError, chat

logger = logging.getLogger(__name__)

SCENES = {
    "cafe": "咖啡店",
    "station": "车站",
    "convenience": "便利店",
    "restaurant": "餐厅",
    "greeting": "初次见面",
    "shopping": "购物",
    "directions": "问路",
    "free": "自由聊天",
}

SCENE_OPENINGS = {
    "cafe": {
        "reply_ja": "いらっしゃいませ。ご注文はお決まりですか。",
        "reply_zh": "欢迎光临。您想好点什么了吗？",
        "reply_ja_ruby": [
            {"s": "いらっしゃいませ。", "r": ""},
            {"s": "ご注文", "r": "ごちゅうもん"},
            {"s": "は", "r": ""},
            {"s": "お決", "r": "おき"},
            {"s": "まりですか。", "r": ""},
        ],
    },
    "station": {
        "reply_ja": "こんにちは。切符を買いませんか。",
        "reply_zh": "你好。要买车票吗？",
        "reply_ja_ruby": [
            {"s": "こんにちは。", "r": ""},
            {"s": "切符", "r": "きっぷ"},
            {"s": "を", "r": ""},
            {"s": "買", "r": "か"},
            {"s": "いませんか。", "r": ""},
        ],
    },
    "convenience": {
        "reply_ja": "いらっしゃいませ。袋はいりますか。",
        "reply_zh": "欢迎光临。需要袋子吗？",
        "reply_ja_ruby": [
            {"s": "いらっしゃいませ。", "r": ""},
            {"s": "袋", "r": "ふくろ"},
            {"s": "は", "r": ""},
            {"s": "いりますか。", "r": ""},
        ],
    },
    "restaurant": {
        "reply_ja": "いらっしゃいませ。何名様ですか。",
        "reply_zh": "欢迎光临。几位？",
        "reply_ja_ruby": [
            {"s": "いらっしゃいませ。", "r": ""},
            {"s": "何名様", "r": "なんめいさま"},
            {"s": "ですか。", "r": ""},
        ],
    },
    "greeting": {
        "reply_ja": "はじめまして。田中です。どうぞよろしくおねがいします。",
        "reply_zh": "初次见面。我是田中。请多关照。",
        "reply_ja_ruby": [
            {"s": "はじめまして。", "r": ""},
            {"s": "田中", "r": "たなか"},
            {"s": "です。どうぞよろしくおねがいします。", "r": ""},
        ],
    },
    "shopping": {
        "reply_ja": "こんにちは。何かお探しですか。",
        "reply_zh": "你好。在找什么吗？",
        "reply_ja_ruby": [
            {"s": "こんにちは。", "r": ""},
            {"s": "何", "r": "なに"},
            {"s": "か", "r": ""},
            {"s": "お探", "r": "おさが"},
            {"s": "しですか。", "r": ""},
        ],
    },
    "directions": {
        "reply_ja": "すみません、道に迷いましたか。手伝いましょうか。",
        "reply_zh": "不好意思，您迷路了吗？需要我帮忙吗？",
        "reply_ja_ruby": [
            {"s": "すみません、", "r": ""},
            {"s": "道", "r": "みち"},
            {"s": "に", "r": ""},
            {"s": "迷", "r": "まよ"},
            {"s": "いましたか。", "r": ""},
            {"s": "手伝", "r": "てつだ"},
            {"s": "いましょうか。", "r": ""},
        ],
    },
    "free": {
        "reply_ja": "こんにちは。今日は何を話しましょうか。",
        "reply_zh": "你好。今天想聊点什么？",
        "reply_ja_ruby": [
            {"s": "こんにちは。", "r": ""},
            {"s": "今日", "r": "きょう"},
            {"s": "は", "r": ""},
            {"s": "何", "r": "なに"},
            {"s": "を", "r": ""},
            {"s": "話", "r": "はな"},
            {"s": "しましょうか。", "r": ""},
        ],
    },
}

SYSTEM_PROMPT = """あなたは日本語の会話相手兼コーチです。学習者は中国語を母語とする初中級者です。
ルール:
- 場面設定を守る。優しい日本人の友人として、自然な長さの2〜3文で返す。
- 学習者の入力が質問でない場合は、返答の最後に会話を続ける自然な質問を必ず1つ入れる。
- 学習者の入力が質問の場合も、答えたあと必要なら相手への質問を1つ返し、会話を終わらせない。
- 学習者の発話が不自然なら否定せず、自然な日本語に直してから会話を続ける。
- 中国語で会話を続けない。日本語で返し、中国語は訳欄だけ。
- 助詞（は/が、に/で、を）やテ形の補足は必要なとき一言だけ中国語で。
- JSON以外を出力しない。コードフェンス禁止。

必ずこの形:
{
  "learner_transcript": "学習者の発話（整形後の日本語）",
  "correction": null,
  "correction_note_zh": null,
    "reply_ja": "AIの日本語返答。自然な2〜3文。最後は必要に応じて相手への質問。ですます。",
  "reply_ja_ruby": [{"s": "今日", "r": "きょう"}, {"s": "は", "r": ""}],
  "reply_zh": "简体中文翻译",
  "new_words": [{"ja": "空", "reading": "そら", "zh": "天空"}]
}
correction は不自然なときだけ正しい文。問題なければ null。
"""

DICT_PROMPT = """你是日语词典教练。学习者是中文母语者。
只解释用户查询的一个词或短语。用 JSON，不要代码围栏，不要多余文字。
{
  "ja": "見出し語（辞書形）",
  "reading": "ひらがな",
  "pos": "动词/名词/形容词/副词/其他",
  "zh": "简体中文意思",
  "examples": [
    {"ja": "例文。", "reading": "よみ", "zh": "中文"}
  ]
}
例文最多2个，短句，N5-N4。如果完全不是日语或中文词，ja 用空字符串。
"""


def _parse_json(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def _conversation_result(raw: str, user_text: str) -> ConversationLLMOut:
    result = ConversationLLMOut.model_validate(_parse_json(raw))
    ruby_text = "".join(token.s for token in result.reply_ja_ruby)
    if result.reply_ja_ruby and ruby_text != result.reply_ja:
        result.reply_ja_ruby = []
    is_question = "?" in user_text or "？" in user_text or user_text.rstrip().endswith("か")
    if not is_question and "?" not in result.reply_ja and "？" not in result.reply_ja:
        raise ValueError("reply does not continue the conversation with a question")
    return result


def opening_for(scene: str) -> ConversationLLMOut:
    data = SCENE_OPENINGS.get(scene) or SCENE_OPENINGS["free"]
    return ConversationLLMOut(
        reply_ja=data["reply_ja"],
        reply_zh=data["reply_zh"],
        reply_ja_ruby=[RubyToken(**t) for t in data["reply_ja_ruby"]],
    )


def fallback_turn(user_text: str, scene: str) -> ConversationLLMOut:
    return ConversationLLMOut(
        learner_transcript=user_text,
        correction=None,
        correction_note_zh=None,
        reply_ja="そうなんですね。今日はどんな一日でしたか？",
        reply_ja_ruby=[],
        reply_zh="原来如此。今天过得怎么样？",
        new_words=[],
    )


def reply_conversation(scene: str, user_text: str, history: list[dict[str, str]]) -> ConversationLLMOut:
    scene_label = SCENES.get(scene, SCENES["free"])
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"今の場面: {scene}（{scene_label}）"},
    ]
    for turn in history[-12:]:
        messages.append(turn)
    messages.append({"role": "user", "content": user_text})

    try:
        raw = chat(messages)
        return _conversation_result(raw, user_text)
    except OpenAIError as exc:
        logger.error("OpenAI conversation request failed: %s", exc)
        if str(exc) == "missing_key":
            return fallback_turn(user_text, scene)
        raise
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("OpenAI conversation response was invalid: %s", exc)
        retry_messages = [
            *messages,
            {
                "role": "system",
                "content": "前の応答を無視し、指定されたJSON形式だけで正しく回答してください。",
            },
        ]
        try:
            return _conversation_result(chat(retry_messages, temperature=0.2), user_text)
        except (json.JSONDecodeError, ValueError) as retry_exc:
            logger.error("OpenAI conversation retry response was invalid: %s", retry_exc)
            return fallback_turn(user_text, scene)


def explain_word(query: str) -> DictionaryItem | None:
    try:
        raw = chat(
            [
                {"role": "system", "content": DICT_PROMPT},
                {"role": "user", "content": query},
            ],
            temperature=0.3,
        )
        data = _parse_json(raw)
        item = DictionaryItem.model_validate(data)
        if not item.ja:
            return None
        return item
    except (OpenAIError, json.JSONDecodeError, ValueError):
        return None
