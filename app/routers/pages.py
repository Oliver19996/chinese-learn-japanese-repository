from datetime import date
import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from markupsafe import Markup
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import TEMPLATE_DIR
from app.db import get_db
from app.deps import get_device
from app.models import ActivityEvent, ConversationSession, ConversationTurn, Device
from app.schemas import StatsOut
from app.services.lessons import dictation_lessons, get_dictation, get_shadowing, shadowing_lessons

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
templates.env.filters["tojson"] = lambda value: Markup(
    json.dumps(value, ensure_ascii=False).replace("<", "\\u003c")
)

TODAY_PHRASES = [
    ("今日もがんばりましょう。", "きょうもがんばりましょう。", "今天也加油吧。"),
    ("美味しいコーヒーを飲みませんか。", "おいしいコーヒーをのみませんか。", "要不要喝杯好喝的咖啡？"),
    ("駅はどこですか。", "えきはどこですか。", "车站在哪里？"),
    ("すみません、お願いします。", "すみません、おねがいします。", "不好意思，拜托了。"),
    ("天気がいいですね。", "てんきがいいですね。", "天气真好啊。"),
    ("少しゆっくり話してください。", "すこしゆっくりはなしてください。", "请说慢一点。"),
    ("これはいくらですか。", "これはいくらですか。", "这个多少钱？"),
    ("また会いましょう。", "またあいましょう。", "下次再见。"),
]


def render(request: Request, name: str, **ctx):
    ctx.setdefault("active", "")
    ctx["request"] = request
    return templates.TemplateResponse(name, ctx)


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    phrase = TODAY_PHRASES[date.today().toordinal() % len(TODAY_PHRASES)]
    return render(
        request,
        "home.html",
        active="home",
        phrase_ja=phrase[0],
        phrase_reading=phrase[1],
        phrase_zh=phrase[2],
    )


@router.get("/conversation", response_class=HTMLResponse)
def conversation_page(request: Request):
    return render(request, "conversation.html", active="conversation")


@router.get("/dictionary", response_class=HTMLResponse)
def dictionary_page(request: Request):
    return render(request, "dictionary.html", active="dictionary")


@router.get("/shadowing", response_class=HTMLResponse)
def shadowing_page(request: Request):
    return render(request, "shadowing.html", active="shadowing", lessons=shadowing_lessons())


@router.get("/shadowing/{lesson_id}", response_class=HTMLResponse)
def shadowing_play(request: Request, lesson_id: str):
    lesson = get_shadowing(lesson_id)
    if not lesson:
        return render(request, "shadowing.html", active="shadowing", lessons=shadowing_lessons())
    return render(request, "shadowing_play.html", active="shadowing", lesson=lesson)


@router.get("/dictation", response_class=HTMLResponse)
def dictation_page(request: Request):
    return render(request, "dictation.html", active="dictation", lessons=dictation_lessons())


@router.get("/dictation/{lesson_id}", response_class=HTMLResponse)
def dictation_play(request: Request, lesson_id: str):
    lesson = get_dictation(lesson_id)
    if not lesson:
        return render(request, "dictation.html", active="dictation", lessons=dictation_lessons())
    return render(request, "dictation_play.html", active="dictation", lesson=lesson)


@router.get("/api/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db), device: Device = Depends(get_device)):
    turns = (
        db.query(func.count(ConversationTurn.id))
        .join(ConversationSession, ConversationTurn.session_id == ConversationSession.id)
        .filter(ConversationSession.device_id == device.id, ConversationTurn.role == "learner")
        .scalar()
        or 0
    )
    shadowing = (
        db.query(func.count(ActivityEvent.id))
        .filter(ActivityEvent.device_id == device.id, ActivityEvent.kind == "shadowing_done")
        .scalar()
        or 0
    )
    dictation = (
        db.query(func.count(ActivityEvent.id))
        .filter(ActivityEvent.device_id == device.id, ActivityEvent.kind == "dictation_correct")
        .scalar()
        or 0
    )
    return StatsOut(
        conversation_turns=int(turns),
        shadowing_done=int(shadowing),
        dictation_correct=int(dictation),
    )
