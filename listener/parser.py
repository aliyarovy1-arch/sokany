from __future__ import annotations

import re


def parse_description(text: str) -> dict:
    lines = [l.strip().replace("**", "") for l in text.strip().splitlines()]
    if not lines:
        return {}

    name = re.sub(
        r"[\U0001F300-\U0001FAFF\U00002702-\U000027B0\U0000FE00-\U0000FE0F‍♀-♂☀-⭕⏏⏩-⏳⌚-⌛⤴-⤵▪-◾⬅-⬇⤴-⤵✅]+",
        "", lines[0],
    ).strip()

    model = None
    model_idx = None
    for i, l in enumerate(lines):
        m = re.match(r"[Мм]одель\s*[:\-]\s*(.+)", l)
        if m:
            model = m.group(1).strip()
            model_idx = i
            break

    box_qty = None
    box_idx = None
    for i, l in enumerate(lines):
        m = re.search(r"[Вв]\s*коробке\s*[:\-]?\s*(\d+)", l)
        if m:
            box_qty = int(m.group(1))
            box_idx = i
            break

    price = None
    for l in lines:
        m = re.search(r"[Цц]ена\s*[:\-]?\s*([\d.]+)", l)
        if m:
            price = float(m.group(1))
            break

    specs_lines = []
    start = (model_idx + 1) if model_idx is not None else 1
    end = box_idx if box_idx is not None else len(lines)
    for l in lines[start:end]:
        stripped = l.strip("✅ \t")
        if stripped and not re.match(r"[Мм]одель\s*[:\-]", stripped):
            specs_lines.append(stripped)
    specs = "\n".join(specs_lines) if specs_lines else None

    return {
        "name": name or None,
        "model": model,
        "specs": specs,
        "box_qty": box_qty,
        "price": price,
    }
