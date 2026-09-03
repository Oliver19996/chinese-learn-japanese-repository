import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AppError, get_device
from app.models import Device, SearchHistory
from app.schemas import AudioOut, DictionaryOut, SpeakIn
from app.services.dictionary import lookup
from app.services.tts import synthesize

router = APIRouter()


@router.get("", response_model=DictionaryOut)
def search(
    q: str = Query(default=""),
    db: Session = Depends(get_db),
    device: Device = Depends(get_device),
):
    query = q.strip()
    items = lookup(query) if query else []
    if query:
        db.add(SearchHistory(id=uuid.uuid4().hex, device_id=device.id, query=query[:128]))
        old = (
            db.query(SearchHistory)
            .filter(SearchHistory.device_id == device.id)
            .order_by(SearchHistory.created_at.desc())
            .offset(20)
            .all()
        )
        for row in old:
            db.delete(row)
        db.commit()
    return DictionaryOut(items=items)


@router.post("/speak", response_model=AudioOut)
def speak(body: SpeakIn, device: Device = Depends(get_device)):
    text = (body.text or "").strip()
    if not text:
        raise AppError("没有可朗读的内容。")
    return AudioOut(audio_url=synthesize(text, cache_key=f"dict_{text[:40]}"))
