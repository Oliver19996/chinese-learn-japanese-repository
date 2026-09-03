import json
import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AppError, get_device
from app.models import ActivityEvent, Device
from app.schemas import AudioOut, LessonTtsIn, ShadowScoreOut
from app.services.lessons import find_item, get_shadowing, lesson_summaries, shadowing_lessons
from app.services.scoring import best_score, comment_zh
from app.services.stt import speech_to_text
from app.services.tts import synthesize

router = APIRouter()


@router.get("/lessons")
def list_lessons():
    return {"lessons": lesson_summaries(shadowing_lessons())}


@router.get("/lessons/{lesson_id}")
def lesson_detail(lesson_id: str):
    lesson = get_shadowing(lesson_id)
    if not lesson:
        raise AppError("课程不存在。", 404)
    return lesson


@router.post("/tts", response_model=AudioOut)
def tts(body: LessonTtsIn, device: Device = Depends(get_device)):
    lesson = get_shadowing(body.lesson_id)
    item = find_item(lesson, body.item_id) if lesson else None
    if not item:
        raise AppError("句子不存在。", 404)
    url = synthesize(item["ja"], cache_key=f"sh_{body.lesson_id}_{body.item_id}")
    return AudioOut(audio_url=url)


@router.post("/score", response_model=ShadowScoreOut)
async def score(
    lesson_id: str = Form(...),
    item_id: str = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    device: Device = Depends(get_device),
):
    lesson = get_shadowing(lesson_id)
    item = find_item(lesson, item_id) if lesson else None
    if not item:
        raise AppError("句子不存在。", 404)
    data = await audio.read()
    heard = speech_to_text(data, audio.content_type or "")
    if heard is None:
        # 无 API 时仍给一个温和的练习分，避免卡住
        heard = ""
        points = 70
        comment = "演示模式：已记录跟读。填写 API 后可评分。"
    else:
        if not heard:
            raise AppError("麦克风音频无法识别，请再试一次。")
        points = best_score(heard, item["ja"], item.get("reading", ""))
        comment = comment_zh(points)
    if points >= 60:
        db.add(
            ActivityEvent(
                id=uuid.uuid4().hex,
                device_id=device.id,
                kind="shadowing_done",
                payload_json=json.dumps({"lesson_id": lesson_id, "item_id": item_id, "score": points}),
            )
        )
        db.commit()
    return ShadowScoreOut(score=points, heard=heard, comment_zh=comment)
