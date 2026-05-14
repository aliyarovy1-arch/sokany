# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Sokany — real-time Telegram channel listener that extracts product data from posts and syncs to Google Sheets. Written in async Python 3.14+ with Telethon.

## Commands

```bash
uv sync                    # Install dependencies
python listener/main.py    # Run the listener (production entry point)
```

## Required Configuration

- `.env` file with: `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_CHANNEL`, `GOOGLE_SA_PATH`, `GOOGLE_SHEET_NAME`
- `credentials/google_sa.json` — Google service account key (scopes: spreadsheets, drive)
- `listener/session.session` — Telethon session file (auto-created on first auth)

## Architecture

Data flow: **Telegram channel → Telethon event handler → regex parser → dedup check → Google Sheets insert**

- `listener/main.py` — async event loop, album buffering (groups messages by `grouped_id`, 3-sec wait), entry point
- `listener/parser.py` — regex extraction of product fields (name, model, specs, box_qty, price) from Russian-language posts
- `listener/sheets.py` — Google Sheets auth via service account, dedup by model (column C), row insert with pricing formulas
- `listener/config.py` — env var loader via python-dotenv

## Key Implementation Details

- **Album buffering**: Telegram sends each photo in a media album as a separate message with the same `grouped_id`. The listener collects them for 3 seconds before processing the group as one product.
- **Deduplication**: checks column C (Модель) in the sheet before inserting. Not atomic — concurrent posts with the same model can race.
- **Pricing formulas**: RUB prices are Excel formulas (`=F*77`, `=G*E`), not computed in Python. The 77 rate is hardcoded in `sheets.py`.
- **Parser expects Russian keywords**: "Модель:", "В коробке:", "Цена:" — case-insensitive regex. Unparseable posts are silently skipped.

## Language

All user-facing strings, logs, and data are in Russian. Code identifiers are in English.
