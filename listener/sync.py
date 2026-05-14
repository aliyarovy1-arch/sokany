from __future__ import annotations

from . import db
from .sheets import get_sheet


def sync() -> None:
    db.init_db()
    sheet = get_sheet()
    models_in_sheet = sheet.col_values(3)[1:]  # skip header

    added = 0
    for model in models_in_sheet:
        model = model.strip()
        if model and not db.model_exists(model):
            db.mark_processed(msg_id=0, model=model)
            added += 1

    print(f"[sync] Синхронизировано: {added} моделей из Google Sheets → SQLite")


if __name__ == "__main__":
    sync()
