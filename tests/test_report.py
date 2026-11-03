from pathlib import Path

import pytest
from openpyxl import load_workbook

from masks_parser.domain import CatalogItem
from masks_parser.matching import CatalogChecker
from masks_parser.report import ReportSummary, XlsxReportWriter
from tests import hilex


def _write(certificate, results, path: Path):
    XlsxReportWriter().write(ReportSummary.from_results(certificate, results), results, path)
    return load_workbook(path)


def _values(sheet) -> list[list[object]]:
    return [list(row) for row in sheet.iter_rows(values_only=True)]


def _item(raw: str, row_id: str = "2") -> CatalogItem:
    return CatalogItem(
        row_id=row_id, manufacturer=hilex.MANUFACTURER, product_group=hilex.GROUP, raw_article=raw, key=raw
    )


@pytest.fixture(scope="module")
def sample_results(loader, hilex_certificate):
    return CatalogChecker(hilex_certificate).check_all(loader.load(hilex.SAMPLES / "catalog_sample.xlsx"))


def test_summary_counts_every_mask_in_register_order(hilex_certificate, sample_results):
    summary = ReportSummary.from_results(hilex_certificate, sample_results)
    assert (summary.total, summary.matched, summary.exceptions) == (214, 123, 91)
    assert list(summary.by_mask) == hilex.MASKS
    assert sum(summary.by_mask.values()) == summary.matched
    assert all(count >= 3 for count in summary.by_mask.values())


def test_summary_keeps_masks_without_hits(hilex_certificate):
    summary = ReportSummary.from_results(hilex_certificate, [])
    assert summary.by_mask == dict.fromkeys(hilex.MASKS, 0)


def test_sample_report(tmp_path, hilex_certificate, sample_results):
    workbook = _write(hilex_certificate, sample_results, tmp_path / "out" / "report.xlsx")
    assert workbook.sheetnames == ["Соответствует", "Исключения", "Сводка"]

    matches = _values(workbook["Соответствует"])
    assert matches[0] == ["Строка", "Производитель", "Товарная группа", "Артикул", "Поисковый ключ", "Маска"]
    assert len(matches) - 1 == 123
    assert ["Строка", "Производитель", "Товарная группа", "Артикул", "Причина"] == _values(
        workbook["Исключения"]
    )[0]
    assert len(_values(workbook["Исключения"])) - 1 == 91

    summary = _values(workbook["Сводка"])
    assert summary[:6] == [
        ["Производитель", hilex.MANUFACTURER],
        ["Товарная группа", hilex.GROUP],
        ["Масок в сертификате", 38],
        ["Строк в выгрузке", 214],
        ["Соответствует", 123],
        ["Исключений", 91],
    ]
    assert summary[7] == ["Маска", "Найдено артикулов"]
    assert [row[0] for row in summary[8:]] == hilex.MASKS


def test_rows_keep_raw_article_and_line_number(tmp_path, hilex_certificate):
    results = CatalogChecker(hilex_certificate).check_all([_item(" 4vb0000 ", "7"), _item("4VB12\n34", "9")])
    workbook = _write(hilex_certificate, results, tmp_path / "r.xlsx")
    assert _values(workbook["Исключения"])[1][0] == 7
    assert _values(workbook["Исключения"])[2][3] == "4VB12\n34"


def test_formula_like_article_is_written_as_text(tmp_path, hilex_certificate):
    results = CatalogChecker(hilex_certificate).check_all([_item("=1+1")])
    cell = _write(hilex_certificate, results, tmp_path / "r.xlsx")["Исключения"]["D2"]
    assert (cell.value, cell.data_type) == ("=1+1", "s")


def test_illegal_xlsx_chars_are_escaped(tmp_path, hilex_certificate):
    results = CatalogChecker(hilex_certificate).check_all([_item("4VB\x0700")])
    assert _write(hilex_certificate, results, tmp_path / "r.xlsx")["Исключения"]["D2"].value == "4VB\\x0700"
