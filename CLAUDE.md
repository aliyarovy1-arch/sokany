# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Sokany — real-time Telegram channel listener that extracts product data from posts and syncs to Google Sheets. Written in async Python 3.14+ with Telethon.

## Commands

```bash
uv sync                    # Install dependencies
python listener/main.py    # Run locally

make up                    # Build & run in Docker (detached)
make down                  # Stop container
make logs                  # Tail container logs
make db                    # sqlite3 shell into the dedup database
```

## Required Configuration

- `.env` file with: `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_CHANNEL`, `GOOGLE_SA_PATH`, `GOOGLE_SHEET_NAME`, optionally `DB_PATH`
- `credentials/google_sa.json` — Google service account key (scopes: spreadsheets, drive)
- `listener/session.session` — Telethon session file (auto-created on first auth)

## Architecture

Data flow: **Telegram channel → Telethon event handler → regex parser → SQLite dedup check → Google Sheets insert + SQLite mark**

On startup, backfills last 100 messages from the channel before switching to live event listening.

- `listener/main.py` — async event loop, album buffering, backfill on startup, entry point
- `listener/parser.py` — regex extraction of product fields (name, model, specs, box_qty, price) from Russian-language posts
- `listener/db.py` — SQLite dedup layer: tracks processed models locally to avoid Sheets API calls
- `listener/sheets.py` — Google Sheets auth via service account, row insert with pricing formulas
- `listener/config.py` — env var loader via python-dotenv

## Key Implementation Details

- **Album buffering**: Telegram sends each photo in a media album as a separate message with the same `grouped_id`. The listener collects them for 3 seconds before processing the group as one product.
- **Deduplication**: SQLite table `products` with `model UNIQUE` constraint. Checked locally before hitting Sheets API. After successful Sheets insert, model is marked in SQLite.
- **Backfill**: on startup, fetches last 100 messages from channel, groups albums, runs them through the same processing pipeline. Already-seen models are skipped via SQLite.
- **Pricing formulas**: RUB prices are Excel formulas (`=F*77`, `=G*E`), not computed in Python. The 77 rate is hardcoded in `sheets.py`.
- **Parser expects Russian keywords**: "Модель:", "В коробке:", "Цена:" — case-insensitive regex. Unparseable posts are silently skipped.

## Language

All user-facing strings, logs, and data are in Russian. Code identifiers are in English.
