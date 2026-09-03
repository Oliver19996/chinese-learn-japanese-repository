from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import AUDIO_DIR, DATA_DIR, STATIC_DIR
from app.db import init_db
from app.deps import AppError
from app.routers import conversation, dictation, dictionary, pages, shadowing

app = FastAPI(title="日语会话 Hanashi", docs_url=None, redoc_url=None)


@app.on_event("startup")
def on_startup() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    init_db()


def _error_payload(message: str, status_code: int) -> JSONResponse:
    return JSONResponse({"error": message}, status_code=status_code)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    return _error_payload(exc.message, exc.status_code)


@app.exception_handler(HTTPException)
async def http_error_handler(_: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        return _error_payload(str(detail["error"]), exc.status_code)
    return _error_payload("出了点问题，请稍后再试。", exc.status_code)


@app.exception_handler(StarletteHTTPException)
async def starlette_error_handler(_: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return _error_payload("页面不存在。", 404)
    return _error_payload("出了点问题，请稍后再试。", exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, __: RequestValidationError):
    return _error_payload("请求无效，请再试一次。", 400)


@app.exception_handler(Exception)
async def catch_all(_: Request, __: Exception):
    return _error_payload("出了点问题，请稍后再试。", 400)


@app.get("/manifest.json")
def manifest():
    return FileResponse(STATIC_DIR / "manifest.json", media_type="application/manifest+json")


@app.get("/sw.js")
def service_worker():
    return FileResponse(STATIC_DIR / "sw.js", media_type="application/javascript")


@app.get("/media/audio/{filename}")
def media_audio(filename: str):
    if "/" in filename or ".." in filename:
        return _error_payload("音频不存在。", 404)
    path = AUDIO_DIR / filename
    if not path.exists() or not path.is_file():
        return _error_payload("音频不存在。", 404)
    media_type = "audio/mpeg" if path.suffix == ".mp3" else "audio/wav"
    return FileResponse(path, media_type=media_type)


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(pages.router)
app.include_router(conversation.router, prefix="/api/conversation")
app.include_router(dictionary.router, prefix="/api/dictionary")
app.include_router(shadowing.router, prefix="/api/shadowing")
app.include_router(dictation.router, prefix="/api/dictation")
