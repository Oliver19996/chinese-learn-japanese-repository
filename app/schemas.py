from pydantic import BaseModel, Field


class ErrorOut(BaseModel):
    error: str


class RubyToken(BaseModel):
    s: str
    r: str = ""


class NewWord(BaseModel):
    ja: str
    reading: str = ""
    zh: str = ""


class ConversationStartIn(BaseModel):
    scene: str = "cafe"


class ConversationResetIn(BaseModel):
    session_id: str


class ConversationLLMOut(BaseModel):
    learner_transcript: str = ""
    correction: str | None = None
    correction_note_zh: str | None = None
    reply_ja: str
    reply_ja_ruby: list[RubyToken] = Field(default_factory=list)
    reply_zh: str = ""
    new_words: list[NewWord] = Field(default_factory=list)


class ConversationStartOut(BaseModel):
    session_id: str
    opening_ja: str
    opening_ruby: list[RubyToken] = Field(default_factory=list)
    opening_zh: str = ""
    audio_url: str


class ConversationTurnOut(ConversationLLMOut):
    session_id: str
    audio_url: str


class DictionaryExample(BaseModel):
    ja: str
    reading: str = ""
    zh: str = ""


class DictionaryItem(BaseModel):
    ja: str
    reading: str = ""
    pos: str = ""
    zh: str = ""
    examples: list[DictionaryExample] = Field(default_factory=list)


class DictionaryOut(BaseModel):
    items: list[DictionaryItem]


class SpeakIn(BaseModel):
    text: str


class AudioOut(BaseModel):
    audio_url: str


class LessonTtsIn(BaseModel):
    lesson_id: str
    item_id: str


class ShadowScoreOut(BaseModel):
    score: int
    heard: str
    comment_zh: str


class DictationGradeIn(BaseModel):
    lesson_id: str
    item_id: str
    answer: str


class DiffToken(BaseModel):
    t: str
    kind: str


class DictationGradeOut(BaseModel):
    score: int
    correct_ja: str
    correct_reading: str = ""
    correct_zh: str = ""
    diff: list[DiffToken]


class StatsOut(BaseModel):
    conversation_turns: int = 0
    shadowing_done: int = 0
    dictation_correct: int = 0
