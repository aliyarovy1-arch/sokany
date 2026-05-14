from __future__ import annotations

import base64
import tempfile
from pathlib import Path

import httpx
from telethon import TelegramClient

from .config import IMGBB_API_KEY

IMGBB_URL = "https://api.imgbb.com/1/upload"


async def upload_to_imgbb(file_path: Path) -> str | None:
    image_b64 = base64.b64encode(file_path.read_bytes()).decode()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            IMGBB_URL,
            data={"key": IMGBB_API_KEY, "image": image_b64},
        )
    if resp.status_code == 200:
        return resp.json()["data"]["url"]
    print(f"[imgbb] Ошибка загрузки: {resp.status_code} {resp.text[:200]}")
    return None


async def get_photo_url(client: TelegramClient, messages: list) -> str | None:
    for msg in messages:
        if msg.photo:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            await client.download_media(msg, file=str(tmp_path))
            try:
                url = await upload_to_imgbb(tmp_path)
            finally:
                tmp_path.unlink(missing_ok=True)
            return url
    return None
