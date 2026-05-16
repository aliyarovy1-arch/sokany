from __future__ import annotations

import asyncio
from collections import defaultdict
from pathlib import Path

from telethon import TelegramClient, events
from telethon.sessions import StringSession

from .config import API_ID, API_HASH, CHANNEL, TELEGRAM_SESSION
from .parser import parse_description
from .photos import get_photo_url
from .sheets import get_sheet, get_existing_models, insert_row, delete_row_by_model
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

    sheet = get_sheet()
    if db.model_exists(model):
        delete_row_by_model(sheet, model)
        db.delete_model(model)
        print(f"[replace] Заменяю модель '{model}'")

    first = messages[0]
    date_str = first.date.strftime("%Y-%m-%d") if first.date else ""

    photo_url = await get_photo_url(client, messages) or ""

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
    print("[backfill] Проверяю последние 10 сообщений...")
    messages = await client.get_messages(CHANNEL, limit=10)

    groups: dict[int, list] = defaultdict(list)
    singles: list = []

    for msg in messages:
        if msg.grouped_id:
            groups[msg.grouped_id].append(msg)
        else:
            singles.append(msg)

    units: list[list] = []
    for group_msgs in groups.values():
        group_msgs.sort(key=lambda m: m.id)
        units.append(group_msgs)
    for msg in singles:
        units.append([msg])

    units.sort(key=lambda unit: unit[0].id)

    for unit in units:
        await process_messages(client, unit)

    print("[backfill] Готово")


KEEPALIVE_INTERVAL = 3600
RECONNECT_DELAY = 10


async def keepalive(client: TelegramClient) -> None:
    while True:
        await asyncio.sleep(KEEPALIVE_INTERVAL)
        try:
            await client.get_me()
            print("[keepalive] Соединение активно")
        except Exception as e:
            print(f"[keepalive] Пинг не прошёл: {e}")


async def main() -> None:
    db.init_db()

    existing = get_existing_models()
    if existing:
        db.bulk_mark_models(existing)
        print(f"[sync] Загружено {len(existing)} моделей из таблицы")

    session = StringSession(TELEGRAM_SESSION) if TELEGRAM_SESSION else SESSION_PATH
    client = TelegramClient(session, API_ID, API_HASH)

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

    while True:
        try:
            await client.start()
            await backfill_recent(client)
            print(f"Слушаю канал {CHANNEL}...")
            asyncio.create_task(keepalive(client))
            await client.run_until_disconnected()
        except Exception as e:
            print(f"[error] Отключение: {e}")
        print(f"[reconnect] Переподключаюсь через {RECONNECT_DELAY}с...")
        await asyncio.sleep(RECONNECT_DELAY)


if __name__ == "__main__":
    asyncio.run(main())
