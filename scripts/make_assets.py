#!/usr/bin/env python3
"""Generate PWA icons and a placeholder wav (stdlib only)."""

from __future__ import annotations

import math
import struct
import wave
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICONS = ROOT / "app" / "static" / "icons"
AUDIO = ROOT / "app" / "static" / "audio"


def chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def write_png(path: Path, size: int) -> None:
    # #C23A2B field with a simple white ring
    raw = bytearray()
    cx = cy = size / 2
    r_outer = size * 0.38
    r_inner = size * 0.26
    for y in range(size):
        raw.append(0)
        for x in range(size):
            dx, dy = x - cx, y - cy
            dist = math.hypot(dx, dy)
            if r_inner <= dist <= r_outer:
                raw.extend((255, 248, 241))
            else:
                raw.extend((194, 58, 43))
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


def write_wav(path: Path) -> None:
    rate = 16000
    n = int(rate * 0.35)
    frames = bytearray()
    for i in range(n):
        env = min(i / 200, 1, (n - i) / 400)
        sample = int(2800 * env * math.sin(2 * math.pi * 523 * i / rate))
        frames.extend(struct.pack("<h", sample))
    with wave.open(str(path), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(bytes(frames))


def main() -> None:
    ICONS.mkdir(parents=True, exist_ok=True)
    AUDIO.mkdir(parents=True, exist_ok=True)
    write_png(ICONS / "icon-192.png", 192)
    write_png(ICONS / "icon-512.png", 512)
    write_wav(AUDIO / "placeholder.wav")
    print("assets ok")


if __name__ == "__main__":
    main()
