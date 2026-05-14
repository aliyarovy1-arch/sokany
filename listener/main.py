from __future__ import annotations

import asyncio
from collections import defaultdict
from pathlib import Path

from telethon import TelegramClient, events

from .config import API_ID, API_HASH, CHANNEL
from .parser import parse_description
from .photos import get_photo_url
from .sheets import get_sheet, insert_row
from . import db

SESSION_PATH = str(Path(__file__).resolve().parent / "session")

album_buffer: dict[int, list] = defaultdict(list)
album_timers: dict[int, asyncio.Task] = {}


async def process_messages(client: TelegramClient, messages: list) -> None:
    text = ""
    for m in messages:
        if m.text:
            text = m.text
            break

    if not text:
        print(f"[skip] Пост без текста (msg_id={messages[0].id})")
        return

    data = parse_description(text)
    model = data.get("model")
    if not model:
        print(f"[skip] Модель не найдена (msg_id={messages[0].id})")
        return

    if db.model_exists(model):
        return

    first = messages[0]
    date_str = first.date.strftime("%Y-%m-%d") if first.date else ""

    photo_url = await get_photo_url(client, messages) or ""

    sheet = get_sheet()
    insert_row(sheet, data, first.id, date_str, photo_url)
    db.mark_processed(first.id, model, photo_url)
    print(f"[ok] Добавлено: {data.get('name')} | модель: {model}")


async def flush_album(client: TelegramClient, grouped_id: int) -> None:
    await asyncio.sleep(3)
    messages = album_buffer.pop(grouped_id, [])
    album_timers.pop(grouped_id, None)
    if messages:
        messages.sort(key=lambda m: m.id)
        await process_messages(client, messages)


async def backfill_recent(client: TelegramClient) -> None:
    print("[backfill] Проверяю последние 100 сообщений...")
    messages = await client.get_messages(CHANNEL, limit=100)

    groups: dict[int, list] = defaultdict(list)
    singles: list = []

    for msg in messages:
        if msg.grouped_id:
            groups[msg.grouped_id].append(msg)
        else:
            singles.append(msg)

    for group_msgs in groups.values():
        group_msgs.sort(key=lambda m: m.id)
        await process_messages(client, group_msgs)

    for msg in sorted(singles, key=lambda m: m.id):
        await process_messages(client, [msg])

    print("[backfill] Готово")


async def main() -> None:
    db.init_db()
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.start()
    await backfill_recent(client)
    print(f"Слушаю канал {CHANNEL}...")

    @client.on(events.NewMessage(chats=CHANNEL))
    async def handler(event):
        msg = event.message

        if msg.grouped_id:
            album_buffer[msg.grouped_id].append(msg)
            old = album_timers.pop(msg.grouped_id, None)
            if old:
                old.cancel()
            album_timers[msg.grouped_id] = asyncio.create_task(
                flush_album(client, msg.grouped_id)
            )
        else:
            await process_messages(client, [msg])

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
