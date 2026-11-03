"""Генерирует тестовую выгрузку каталога для проверки сертификата HI-LEX.

Результат:
  samples/catalog_sample.csv   — выгрузка (UTF-8 с BOM, разделитель «;»)
  samples/catalog_sample.xlsx  — то же в Excel (если установлен openpyxl)
  samples/catalog_expected.csv — эталон: ожидаемый результат и причина по каждой строке

Генерация детерминирована (фиксированный seed), файлы можно пересобирать.
"""

import csv
import random
from pathlib import Path

SEED = 20261103
OUT_DIR = Path(__file__).resolve().parent.parent / "samples"

MANUFACTURER = "HI-LEX CORPORATION"
GROUP = "Тросы стояночного тормоза"
PREFIXES = (
    "4VB 4JB 4AB 9TB 4TB 4HB 9CB 9NB 4GB 4RB 4PB 9VB 4UB 4CB 4NB 4DB 9AB 4FB 4BB "
    "4ZB 9HB 4MB 9DB 9ZB 1PB 5PB 9JB 2HB 5CB 2JB 2PB 9RB 9YB 2KB 9GB 2YB 7HB 9BB"
).split()
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

MATCH = "Соответствует"
EXCEPTION = "Исключение"

OTHER_MANUFACTURERS = ["TRW", "BOSCH", "ATE", "TEXTAR", "ADRIAUTO"]
OTHER_GROUPS = ["Тросы сцепления", "Тросы газа", "Колодки тормозные"]

# Ручные случаи: (производитель, группа, артикул, наименование, ожидание, причина).
# Сначала контрольные примеры из ТЗ, затем дополнительные граничные случаи.
EDGE_CASES = [
    # --- контрольные примеры из ТЗ ---
    (MANUFACTURER, GROUP, "4VB0000", "Трос ручника задний", MATCH, "Префикс 4VB и четыре цифры"),
    (MANUFACTURER, GROUP, "9BBA1Z9", "Трос ручника левый", MATCH, "Префикс 9BB и четыре допустимых символа"),
    (MANUFACTURER, GROUP, "4VB123", "Трос ручника", EXCEPTION, "После префикса три символа"),
    (MANUFACTURER, GROUP, "4VB12345", "Трос ручника", EXCEPTION, "После префикса пять символов"),
    (MANUFACTURER, GROUP, "4VB12-3", "Трос ручника", EXCEPTION, "Дефис внутри артикула"),
    (MANUFACTURER, GROUP, "4QB1234", "Трос ручника", EXCEPTION, "Префикс отсутствует в перечне"),
    (MANUFACTURER, GROUP, "4VB12А3", "Трос ручника", EXCEPTION, "Кириллическая А внутри артикула"),
    # --- нормализация: должно пройти ---
    (
        MANUFACTURER,
        GROUP,
        "4jb7k2m",
        "Трос ручника правый",
        MATCH,
        "Нижний регистр латиницы переводится в верхний",
    ),
    (MANUFACTURER, GROUP, "  4AB1C2D  ", "Трос ручника", MATCH, "Пробелы по краям обрезаются"),
    (MANUFACTURER, GROUP, " 9TB55AA ", "Трос ручника", MATCH, "NBSP по краям заменяется и обрезается"),
    (MANUFACTURER, GROUP, "2YBOOOO", "Трос ручника", MATCH, "Латинская O допустима в хвосте"),
    (MANUFACTURER, GROUP, "7HBIIII", "Трос ручника", MATCH, "Латинская I допустима в хвосте"),
    (MANUFACTURER, GROUP, "1PB0001", "Трос ручника", MATCH, "Префикс с цифрой 1"),
    # --- нормализация: должно уйти в исключения ---
    (MANUFACTURER, GROUP, "4VB 1234", "Трос ручника", EXCEPTION, "Внутренний пробел"),
    (MANUFACTURER, GROUP, "4VB.1234", "Трос ручника", EXCEPTION, "Точка внутри артикула"),
    (MANUFACTURER, GROUP, "4VB1234\n", "Трос ручника", EXCEPTION, "Перевод строки в артикуле"),
    (MANUFACTURER, GROUP, "4VB12\n34", "Трос ручника", EXCEPTION, "Перевод строки внутри артикула"),
    (
        MANUFACTURER,
        GROUP,
        "4VB 1234",
        "Трос ручника",
        EXCEPTION,
        "NBSP внутри артикула (становится внутренним пробелом)",
    ),
    (MANUFACTURER, GROUP, "А4B1234", "Трос ручника", EXCEPTION, "Кириллическая А в префиксе"),
    (MANUFACTURER, GROUP, "4VВ1234", "Трос ручника", EXCEPTION, "Кириллическая В в префиксе"),
    (
        MANUFACTURER,
        GROUP,
        "IPB0001",
        "Трос ручника",
        EXCEPTION,
        "Префикс IPB (буква I вместо 1) отсутствует в перечне",
    ),
    (MANUFACTURER, GROUP, "4VB12_4", "Трос ручника", EXCEPTION, "Подчёркивание внутри артикула"),
    (MANUFACTURER, GROUP, "4VB12/4", "Трос ручника", EXCEPTION, "Косая черта внутри артикула"),
    (MANUFACTURER, GROUP, "4vb12é4", "Трос ручника", EXCEPTION, "Латинская буква с диакритикой"),
    (MANUFACTURER, GROUP, "", "Трос ручника", EXCEPTION, "Пустой артикул"),
    (MANUFACTURER, GROUP, "   ", "Трос ручника", EXCEPTION, "Артикул из одних пробелов"),
    (MANUFACTURER, GROUP, "4VB", "Трос ручника", EXCEPTION, "Только префикс"),
    (MANUFACTURER, GROUP, "4VB12344VB1234", "Трос ручника", EXCEPTION, "Два артикула слиты в одну строку"),
    (MANUFACTURER, GROUP, "4VB1234,4JB0000", "Трос ручника", EXCEPTION, "Два артикула через запятую"),
    (MANUFACTURER, GROUP, "B4VB123", "Трос ручника", EXCEPTION, "Префикс не с начала строки"),
    # --- производитель и группа проверяются отдельно ---
    ("TRW", GROUP, "4VB1111", "Трос ручника", EXCEPTION, "Другой производитель при подходящем артикуле"),
    (
        MANUFACTURER,
        "Тросы сцепления",
        "4VB2222",
        "Трос сцепления",
        EXCEPTION,
        "Другая товарная группа при подходящем артикуле",
    ),
    ("", GROUP, "4VB3333", "Трос ручника", EXCEPTION, "Производитель не указан"),
    (MANUFACTURER, "", "4VB4444", "Трос ручника", EXCEPTION, "Товарная группа не указана"),
    # Спорный случай: регистр в названии производителя. Принято — сравнение без учёта
    # регистра и краевых пробелов; если заказчик требует точного совпадения, поменять на EXCEPTION.
    (
        "Hi-Lex Corporation ",
        GROUP,
        "4CB5555",
        "Трос ручника",
        MATCH,
        "Производитель отличается регистром и краевым пробелом (сравнение без учёта регистра)",
    ),
]


def random_tail(rng: random.Random) -> str:
    return "".join(rng.choice(ALPHABET) for _ in range(4))


def build_rows() -> list[dict]:
    rng = random.Random(SEED)
    cases = list(EDGE_CASES)
    used = {c[2] for c in cases}

    def unique(article_factory):
        while True:
            a = article_factory()
            if a not in used:
                used.add(a)
                return a

    # По три валидных артикула на каждый из 38 префиксов — проверка, что ни один не потерян.
    for prefix in PREFIXES:
        for _ in range(3):
            a = unique(lambda p=prefix: p + random_tail(rng))
            cases.append(
                (
                    MANUFACTURER,
                    GROUP,
                    a,
                    "Трос стояночного тормоза",
                    MATCH,
                    f"Префикс {prefix} и четыре допустимых символа",
                )
            )

    # Похожие, но отсутствующие в перечне префиксы.
    fake_prefixes = ["4QB", "4XB", "3VB", "6HB", "9XB", "4VA", "4VC", "0PB", "8HB", "2AB"]
    for prefix in fake_prefixes:
        a = unique(lambda p=prefix: p + random_tail(rng))
        cases.append(
            (
                MANUFACTURER,
                GROUP,
                a,
                "Трос стояночного тормоза",
                EXCEPTION,
                f"Префикс {prefix} отсутствует в перечне",
            )
        )

    # Шум: другие производители и группы с артикулами своих форматов.
    for _ in range(40):
        mfr = rng.choice(OTHER_MANUFACTURERS)
        grp = rng.choice(OTHER_GROUPS + [GROUP])
        a = unique(lambda: "".join(rng.choice(ALPHABET) for _ in range(rng.randint(5, 10))))
        cases.append((mfr, grp, a, "Прочий товар", EXCEPTION, "Другой производитель"))
    for _ in range(15):
        grp = rng.choice(OTHER_GROUPS)
        a = unique(lambda: rng.choice(PREFIXES) + random_tail(rng))
        cases.append(
            (MANUFACTURER, grp, a, "Прочий трос", EXCEPTION, "Другая товарная группа при подходящем артикуле")
        )

    rng.shuffle(cases)
    return [
        {
            "row_id": i,
            "Производитель": mfr,
            "Товарная группа": grp,
            "Артикул": art,
            "Наименование": name,
            "expected": exp,
            "reason": reason,
        }
        for i, (mfr, grp, art, name, exp, reason) in enumerate(cases, start=1)
    ]


CATALOG_COLS = ["row_id", "Производитель", "Товарная группа", "Артикул", "Наименование"]


def write_csv(rows: list[dict]) -> None:
    with open(OUT_DIR / "catalog_sample.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(CATALOG_COLS)
        for r in rows:
            w.writerow([r[c] for c in CATALOG_COLS])
    with open(OUT_DIR / "catalog_expected.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["row_id", "Артикул", "Ожидаемый результат", "Причина"])
        for r in rows:
            w.writerow([r["row_id"], r["Артикул"], r["expected"], r["reason"]])


def write_xlsx(rows: list[dict]) -> bool:
    try:
        from openpyxl import Workbook
    except ImportError:
        return False
    wb = Workbook()
    ws = wb.active
    ws.title = "Выгрузка"
    ws.append(CATALOG_COLS)
    for r in rows:
        ws.append([r[c] for c in CATALOG_COLS])
    for cell in ws["D"][1:]:
        cell.number_format = "@"  # артикул всегда текст, без автоприведения к числу
    for col, width in zip("ABCDE", (8, 24, 30, 18, 30), strict=True):
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "A2"
    wb.save(OUT_DIR / "catalog_sample.xlsx")
    return True


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    rows = build_rows()
    write_csv(rows)
    has_xlsx = write_xlsx(rows)
    matches = sum(r["expected"] == MATCH for r in rows)
    print(f"Строк: {len(rows)}, ожидается соответствий: {matches}, исключений: {len(rows) - matches}")
    print(
        "Файлы:",
        ", ".join(
            ["catalog_sample.csv", "catalog_expected.csv"] + (["catalog_sample.xlsx"] if has_xlsx else [])
        ),
    )


if __name__ == "__main__":
    main()
