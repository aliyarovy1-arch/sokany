# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Sokany — real-time Telegram channel listener that extracts product data from posts and syncs to Google Sheets. Written in async Python 3.14+ with Telethon.

## Commands

```bash
uv sync                    # Install dependencies
python listener/main.py    # Run locally (needs .env)
python generate_session.py # Generate StringSession for headless deploy

make up                    # Build & run in Docker (detached)
make down                  # Stop container
make logs                  # Tail container logs
make db                    # sqlite3 shell into the dedup database
```

## Required Configuration

`.env` file with:
- `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_CHANNEL` — Telegram credentials
- `IMGBB_API_KEY` — for uploading product photos
- `GOOGLE_SHEET_NAME` — target spreadsheet name
- `GOOGLE_SA_PATH` or `GOOGLE_SA_JSON` — path to SA key file, or the JSON string itself (for Railway/headless)
- `TELEGRAM_SESSION` — optional StringSession string; if empty, uses file-based session at `listener/session.session`
- `DB_PATH` — optional, defaults to `data/sokany.db`

## Architecture

Data flow: **Telegram channel → Telethon event handler → regex parser → SQLite dedup check → imgbb photo upload → Google Sheets insert + SQLite mark**

Startup sequence:
1. Init SQLite schema
2. Fetch all models from Google Sheets column C → bulk-insert into SQLite (sync)
3. Register Telethon live event handler on `CHANNEL`

Backfill (`backfill_recent`) exists but is currently commented out in `main()`.

### Modules

- `listener/main.py` — async event loop, album buffering, backfill, entry point
- `listener/parser.py` — regex extraction of product fields (name, model, specs, box_qty, price)
- `listener/photos.py` — downloads first photo from album, uploads to imgbb, returns URL
- `listener/db.py` — SQLite dedup layer: `products` table with `model UNIQUE`
- `listener/sheets.py` — Google Sheets auth, row insert/delete, reads existing models
- `listener/config.py` — env var loader via python-dotenv

## Key Implementation Details

- **Album buffering**: Telegram sends each photo in a media album as a separate message with the same `grouped_id`. The listener collects them for 3 seconds before processing the group as one product.
- **Upsert logic**: if a model already exists in SQLite, the old Sheets row is found by model (column C) and deleted, then SQLite row is deleted — before re-inserting the new data. This replaces stale entries rather than skipping or duplicating.
- **Sheets row layout** (columns A–L): Photo (`=IMAGE(url)`), Name, Model, Specs, BoxQty, PriceUSD, RUB/unit (`=F2*77`), RUB/box (`=G2*E2`), Date, Dimensions, blank, blank. New rows always insert at index 2 (right below the header).
- **Pricing formulas are hardcoded to row 2**: `=F2*77` and `=G2*E2` — because `insert_row` always inserts at row 2, formulas reference the row being inserted. If insertion position changes, the formulas break.
- **Exchange rate 77** is hardcoded in `sheets.py:insert_row`.
- **Parser expects Russian keywords**: "Модель:", "В коробке:", "Цена:" — case-insensitive regex. Unparseable posts are silently skipped.

## Language

All user-facing strings, logs, and data are in Russian. Code identifiers are in English.
