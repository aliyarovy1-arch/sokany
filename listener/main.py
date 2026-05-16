from __future__ import annotations

import asyncio
from pathlib import Path

from telethon import TelegramClient
from telethon.sessions import StringSession

from .config import API_ID, API_HASH, CHANNEL, TELEGRAM_SESSION, POLL_INTERVAL
from .parser import parse_description
from .photos import get_photo_url
from .sheets import get_sheet, get_existing_models, insert_row, delete_row_by_model
from . import db

SESSION_PATH = str(Path(__file__).resolve().parent / "session")


def group_messages(messages: list) -> list[list]:
    albums: dict[int, list] = {}
    singles: list[list] = []

    for msg in messages:
        if msg.grouped_id:
            albums.setdefault(msg.grouped_id, []).append(msg)
        else:
            singles.append([msg])

    groups = []
    for group_msgs in albums.values():
        group_msgs.sort(key=lambda m: m.id)
        groups.append(group_msgs)
    groups.extend(singles)
    groups.sort(key=lambda g: g[0].id)
    return groups


async def process_group(client: TelegramClient, messages: list, sheet) -> None:
    msg_ids = [m.id for m in messages]
    grouped_id = messages[0].grouped_id

    text = ""
    for m in messages:
        if m.text:
            text = m.text
            break

    if not text:
        print(f"[skip] Пост без текста (msg_id={messages[0].id})")
        db.mark_msg_ids_processed(msg_ids, grouped_id, None)
        return

    data = parse_description(text)
    model = data.get("model")
    if not model:
        print(f"[skip] Модель не найдена (msg_id={messages[0].id})")
        db.mark_msg_ids_processed(msg_ids, grouped_id, None)
        return

    if db.model_exists(model):
        delete_row_by_model(sheet, model)
        db.delete_model(model)
        print(f"[replace] Заменяю модель '{model}'")

    first = messages[0]
    date_str = first.date.strftime("%Y-%m-%d") if first.date else ""

    photo_url = await get_photo_url(client, messages) or ""

    insert_row(sheet, data, first.id, date_str, photo_url)
    db.mark_processed(first.id, model, photo_url)
    db.mark_msg_ids_processed(msg_ids, grouped_id, model)
    print(f"[ok] Добавлено: {data.get('name')} | модель: {model}")


async def poll_once(client: TelegramClient) -> None:
    messages = await client.get_messages(CHANNEL, limit=40)
    if not messages:
        print("[poll] Нет сообщений")
        return

    groups = group_messages(messages)
    sheet = get_sheet()

    new_count = 0
    for group in groups:
        if db.msg_id_processed(group[0].id):
            continue
        await process_group(client, group, sheet)
        new_count += 1

    print(f"[poll] Обработано {new_count} новых постов из {len(groups)}")


async def main() -> None:
    db.init_db()
    db.migrate_existing_msg_ids()

    existing = get_existing_models()
    if existing:
        db.bulk_mark_models(existing)
        print(f"[sync] Загружено {len(existing)} моделей из таблицы")

    session = StringSession(TELEGRAM_SESSION) if TELEGRAM_SESSION else SESSION_PATH
    client = TelegramClient(session, API_ID, API_HASH)
    await client.start()
    print(f"[start] Клиент запущен, поллинг каждые {POLL_INTERVAL}с")

    try:
        await poll_once(client)
    except Exception as e:
        print(f"[error] Ошибка при поллинге: {e}")
    await client.disconnect()

    while True:
        await asyncio.sleep(POLL_INTERVAL)
        try:
            await client.connect()
            await poll_once(client)
        except Exception as e:
            print(f"[error] Ошибка при поллинге: {e}")
        finally:
            await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
