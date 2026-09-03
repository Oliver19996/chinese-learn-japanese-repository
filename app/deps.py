from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Device


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


def require_device_id(x_device_id: str = Header(default="", alias="X-Device-Id")) -> str:
    device_id = (x_device_id or "").strip()
    if not device_id:
        raise HTTPException(status_code=400, detail={"error": "缺少设备信息，请刷新页面。"})
    return device_id


def get_device(
    db: Session = Depends(get_db),
    device_id: str = Depends(require_device_id),
) -> Device:
    device = db.get(Device, device_id)
    if device is None:
        device = Device(id=device_id)
        db.add(device)
        db.commit()
        db.refresh(device)
    return device
