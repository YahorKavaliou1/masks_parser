"""Генерирует синтетический масочный сертификат той же структуры, что «правила масок HI-LEX».

Результат: samples/certificate_sample.docx. Запуск из корня проекта:
    python -m scripts.make_sample_certificate

`build_certificate` используется и в тестах, чтобы собирать сертификаты с расхождениями.
"""

from collections.abc import Mapping, Sequence
from pathlib import Path

from docx import Document

from scripts.make_sample_catalog import GROUP, MANUFACTURER, OUT_DIR, PREFIXES

MASKS = tuple(p + "****" for p in PREFIXES)


def _split(mask: str) -> tuple[str, str]:
    """Маска «префикс + звёздочки» → (префикс, regex хвоста)."""
    prefix = mask.rstrip("*")
    n = len(mask) - len(prefix)
    return prefix, "[A-Z0-9]" + (f"{{{n}}}" if n > 1 else "")


def build_certificate(
    path: Path,
    *,
    masks: Sequence[str] = MASKS,
    manufacturer: str = MANUFACTURER,
    group: str = GROUP,
    listed: Sequence[str] | None = None,
    combined: str | None = None,
    declared: int | None = None,
    row_regex: Mapping[str, str] | None = None,
    with_table: bool = True,
) -> Path:
    """Собирает сертификат. По умолчанию все разделы согласованы; аргументы позволяют их «испортить»."""
    listed = masks if listed is None else listed
    declared = len(masks) if declared is None else declared
    if combined is None:
        tail = _split(masks[0])[1]
        combined = "^(?:" + "|".join(_split(m)[0] for m in masks) + ")" + tail + "$"
    row_regex = row_regex or {}

    doc = Document()
    doc.add_heading(f"Маски артикулов {manufacturer}", level=1)
    doc.add_paragraph(
        f"Документ описывает {declared} масок артикулов, на которые распространяется сертификат."
    )
    doc.add_paragraph("«*» — один символ: цифра 0–9 или заглавная латинская буква A–Z.")
    doc.add_paragraph(f"{group} производства {manufacturer}, артикулы которых соответствуют маскам:")
    doc.add_paragraph(", ".join(listed) + ".")

    doc.add_heading("Реестр масок", level=2)
    doc.add_paragraph(f"Производитель – {manufacturer}. Продукция – {group}.")
    if with_table:
        table = doc.add_table(rows=1, cols=4)
        for cell, title in zip(
            table.rows[0].cells, ("Производитель", "Маска артикула", "Regex", "Префикс"), strict=True
        ):
            cell.text = title
        for mask in masks:
            prefix, tail = _split(mask)
            regex = row_regex.get(mask, f"^{prefix}{tail}$")
            for cell, value in zip(table.add_row().cells, (manufacturer, mask, regex, prefix), strict=True):
                cell.text = value

    doc.add_heading("Условие проверки", level=2)
    doc.add_paragraph(f"Условие отбора: производитель = {manufacturer}; товарная группа = {group}.")
    doc.add_paragraph(combined)
    doc.add_paragraph(f"Каждый принятый артикул соответствует ровно одной из {declared} масок.")
    doc.save(str(path))
    return path


if __name__ == "__main__":
    out = build_certificate(OUT_DIR / "certificate_sample.docx")
    print(f"Файл: {out.relative_to(OUT_DIR.parent)}")
