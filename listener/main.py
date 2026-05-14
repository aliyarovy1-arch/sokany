from __future__ import annotations

import asyncio
from collections import defaultdict
from pathlib import Path

from telethon import TelegramClient, events

from .config import API_ID, API_HASH, CHANNEL
from .parser import parse_description
from .sheets import get_sheet, model_exists, insert_row

SESSION_PATH = str(Path(__file__).resolve().parent / "session")

album_buffer: dict[int, list] = defaultdict(list)
album_timers: dict[int, asyncio.Task] = {}


async def process_messages(messages: list) -> None:
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

    sheet = get_sheet()

    if model_exists(sheet, model):
        print(f"[skip] Модель '{model}' уже есть в таблице")
        return

    first = messages[0]
    date_str = first.date.strftime("%Y-%m-%d") if first.date else ""

    insert_row(sheet, data, first.id, date_str)
    print(f"[ok] Добавлено: {data.get('name')} | модель: {model}")


async def flush_album(grouped_id: int) -> None:
    await asyncio.sleep(3)
    messages = album_buffer.pop(grouped_id, [])
    album_timers.pop(grouped_id, None)
    if messages:
        messages.sort(key=lambda m: m.id)
        await process_messages(messages)


async def main() -> None:
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.start()
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
                flush_album(msg.grouped_id)
            )
        else:
            await process_messages([msg])

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
