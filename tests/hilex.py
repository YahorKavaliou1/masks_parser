"""Общие тестовые данные: маски сертификата HI-LEX и тестовая выгрузка из samples/."""

import csv
import re
from pathlib import Path

MANUFACTURER = "HI-LEX CORPORATION"
GROUP = "Тросы стояночного тормоза"

PREFIXES = (
    "4VB 4JB 4AB 9TB 4TB 4HB 9CB 9NB 4GB 4RB 4PB 9VB 4UB 4CB 4NB 4DB 9AB 4FB 4BB "
    "4ZB 9HB 4MB 9DB 9ZB 1PB 5PB 9JB 2HB 5CB 2JB 2PB 9RB 9YB 2KB 9GB 2YB 7HB 9BB"
).split()
MASKS = [p + "****" for p in PREFIXES]

# Итоговое выражение из раздела «Точное условие машинной проверки» ТЗ.
TZ_REGEX = re.compile(r"^(?:" + "|".join(PREFIXES) + r")[A-Z0-9]{4}$")

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def _read_csv(name: str) -> list[dict[str, str]]:
    with open(SAMPLES / name, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def sample_rows() -> list[dict[str, str]]:
    """Строки тестовой выгрузки, дополненные эталонным результатом и причиной."""
    expected = {r["row_id"]: r for r in _read_csv("catalog_expected.csv")}
    return [
        row | {"expected": expected[row["row_id"]]["Ожидаемый результат"]}
        for row in _read_csv("catalog_sample.csv")
    ]
