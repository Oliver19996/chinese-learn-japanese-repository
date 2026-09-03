import json
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AppError, get_device
from app.models import ActivityEvent, Device
from app.schemas import AudioOut, DictationGradeIn, DictationGradeOut, LessonTtsIn
from app.services.lessons import dictation_lessons, find_item, get_dictation, lesson_summaries
from app.services.scoring import best_score, char_diff
from app.services.tts import synthesize

router = APIRouter()


@router.get("/lessons")
def list_lessons():
    return {"lessons": lesson_summaries(dictation_lessons())}


@router.get("/lessons/{lesson_id}")
def lesson_detail(lesson_id: str):
    lesson = get_dictation(lesson_id)
    if not lesson:
        raise AppError("课程不存在。", 404)
    return lesson


@router.post("/tts", response_model=AudioOut)
def tts(body: LessonTtsIn, device: Device = Depends(get_device)):
    lesson = get_dictation(body.lesson_id)
    item = find_item(lesson, body.item_id) if lesson else None
    if not item:
        raise AppError("题目不存在。", 404)
    url = synthesize(item["ja"], cache_key=f"dt_{body.lesson_id}_{body.item_id}")
    return AudioOut(audio_url=url)


@router.post("/grade", response_model=DictationGradeOut)
def grade(
    body: DictationGradeIn,
    db: Session = Depends(get_db),
    device: Device = Depends(get_device),
):
    lesson = get_dictation(body.lesson_id)
    item = find_item(lesson, body.item_id) if lesson else None
    if not item:
        raise AppError("题目不存在。", 404)
    answer = (body.answer or "").strip()
    if not answer:
        raise AppError("请写下你听到的日语。")
    points = best_score(answer, item["ja"], item.get("reading", ""))
    if points >= 80:
        db.add(
            ActivityEvent(
                id=uuid.uuid4().hex,
                device_id=device.id,
                kind="dictation_correct",
                payload_json=json.dumps({"lesson_id": body.lesson_id, "item_id": body.item_id}),
            )
        )
        db.commit()
    return DictationGradeOut(
        score=points,
        correct_ja=item["ja"],
        correct_reading=item.get("reading", ""),
        correct_zh=item.get("zh", ""),
        diff=char_diff(answer, item["ja"]),
    )
