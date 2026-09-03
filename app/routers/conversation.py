from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AppError, get_device
from app.models import ActivityEvent, ConversationSession, ConversationTurn, Device
from app.schemas import (
    ConversationResetIn,
    ConversationStartIn,
    ConversationStartOut,
    ConversationTurnOut,
)
from app.services.llm import opening_for, reply_conversation
from app.services.stt import speech_to_text
from app.services.tts import synthesize

router = APIRouter()


def _new_id() -> str:
    return uuid.uuid4().hex


def _history(db: Session, session_id: str) -> list[dict[str, str]]:
    rows = (
        db.query(ConversationTurn)
        .filter(ConversationTurn.session_id == session_id)
        .order_by(ConversationTurn.created_at.asc())
        .all()
    )
    messages: list[dict[str, str]] = []
    for row in rows[-12:]:
        role = "assistant" if row.role == "ai" else "user"
        messages.append({"role": role, "content": row.text_ja})
    return messages


@router.post("/start", response_model=ConversationStartOut)
def start(
    body: ConversationStartIn,
    db: Session = Depends(get_db),
    device: Device = Depends(get_device),
):
    session = ConversationSession(id=_new_id(), device_id=device.id, scene=body.scene)
    db.add(session)
    opening = opening_for(body.scene)
    audio_url = synthesize(opening.reply_ja, cache_key=f"open_{body.scene}")
    db.add(
        ConversationTurn(
            id=_new_id(),
            session_id=session.id,
            role="ai",
            text_ja=opening.reply_ja,
            text_zh=opening.reply_zh,
            audio_path=audio_url,
        )
    )
    db.commit()
    return ConversationStartOut(
        session_id=session.id,
        opening_ja=opening.reply_ja,
        opening_ruby=opening.reply_ja_ruby,
        opening_zh=opening.reply_zh,
        audio_url=audio_url,
    )


@router.post("/turn", response_model=ConversationTurnOut)
async def turn(
    session_id: str = Form(...),
    text: str | None = Form(default=None),
    audio: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    device: Device = Depends(get_device),
):
    session = db.get(ConversationSession, session_id)
    if not session or session.device_id != device.id:
        raise AppError("对话不存在，请开始新对话。")

    spoken = (text or "").strip()
    if audio is not None:
        data = await audio.read()
        if data:
            heard = speech_to_text(data, audio.content_type or "")
            if heard is None and not spoken:
                raise AppError("语音识别未配置。请先填写 API 密钥，或改用键盘输入。")
            if heard == "" and not spoken:
                raise AppError("麦克风音频无法识别，请再试一次。")
            if heard:
                spoken = heard
    if not spoken:
        raise AppError("请说话或输入日语。")

    result = reply_conversation(session.scene, spoken, _history(db, session.id))
    audio_url = synthesize(result.reply_ja)

    db.add(
        ConversationTurn(
            id=_new_id(),
            session_id=session.id,
            role="learner",
            text_ja=result.learner_transcript or spoken,
            text_zh="",
            correction=result.correction,
        )
    )
    db.add(
        ConversationTurn(
            id=_new_id(),
            session_id=session.id,
            role="ai",
            text_ja=result.reply_ja,
            text_zh=result.reply_zh,
            audio_path=audio_url,
        )
    )
    db.add(
        ActivityEvent(
            id=_new_id(),
            device_id=device.id,
            kind="conversation_turn",
            payload_json=json.dumps({"scene": session.scene}),
        )
    )
    db.commit()
    return ConversationTurnOut(session_id=session.id, audio_url=audio_url, **result.model_dump())


@router.post("/reset")
def reset(
    body: ConversationResetIn,
    db: Session = Depends(get_db),
    device: Device = Depends(get_device),
):
    session = db.get(ConversationSession, body.session_id)
    if session and session.device_id == device.id:
        db.query(ConversationTurn).filter(ConversationTurn.session_id == session.id).delete()
        db.delete(session)
        db.commit()
    return {"ok": True}
