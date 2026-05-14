from __future__ import annotations

import gspread
from google.oauth2.service_account import Credentials

from .config import SA_PATH, SHEET_NAME

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_sheet() -> gspread.Worksheet:
    creds = Credentials.from_service_account_file(str(SA_PATH), scopes=SCOPES)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open(SHEET_NAME)
    return spreadsheet.sheet1


def delete_row_by_model(sheet: gspread.Worksheet, model: str) -> None:
    cell = sheet.find(model, in_column=3)
    if cell is not None:
        sheet.delete_rows(cell.row)


def insert_row(
    sheet: gspread.Worksheet,
    data: dict,
    msg_id: int,
    date_str: str,
    photo_url: str = "",
) -> None:
    post_link = f"https://t.me/Sokany_official/{msg_id}"
    photo_cell = f'=IMAGE("{photo_url}")' if photo_url else post_link

    row = [
        photo_cell,                  # A: Фото
        data.get("name") or "",      # B: Наименование
        data.get("model") or "",     # C: Модель
        data.get("specs") or "",     # D: Характеристики и описание
        data.get("box_qty") or "",   # E: Кол-во в коробке
        data.get("price") or "",     # F: Цена за ед. в usd
        "=F2*77",                    # G: Зак Стоимость в руб. за ед.
        "=G2*E2",                    # H: Зак Стоимость коробки
        date_str,                    # I: Дата обновления
        "",                          # J: Габаритные размеры
        "",                          # K: Стоимость в руб. за ед.
        "",                          # L: Стоимость коробки
    ]

    sheet.insert_row(row, index=2, value_input_option="USER_ENTERED")
