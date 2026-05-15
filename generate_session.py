"""Generate a Telethon StringSession for use in TELEGRAM_SESSION env var."""

import asyncio

from telethon import TelegramClient
from telethon.sessions import StringSession

from listener.config import API_ID, API_HASH


async def main() -> None:
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.start()
    print("\nTELEGRAM_SESSION=", client.session.save(), sep="")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
