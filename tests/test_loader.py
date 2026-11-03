from pathlib import Path

import pytest
from openpyxl import Workbook

from masks_parser.catalog import CatalogFormatError
from tests import hilex


def _write_xlsx(path: Path, rows: list[list[object]]) -> Path:
    workbook = Workbook()
    for row in rows:
        workbook.active.append(row)
    workbook.save(path)
    return path


def test_csv_and_xlsx_samples_load_identically(loader):
    from_csv = loader.load(hilex.SAMPLES / "catalog_sample.csv")
    from_xlsx = loader.load(hilex.SAMPLES / "catalog_sample.xlsx")
    assert len(from_csv) == 214
    assert from_csv == from_xlsx


def test_raw_article_is_kept_and_key_is_normalized(loader):
    items = {i.raw_article: i for i in loader.load(hilex.SAMPLES / "catalog_sample.xlsx")}
    assert items[" 9TB55AA "].key == "9TB55AA"
    assert items["4VB1234\n"].key == "4VB1234\n"
    assert items["4jb7k2m"].key == "4JB7K2M"


def test_row_id_is_line_number(loader):
    items = loader.load(hilex.SAMPLES / "catalog_sample.csv")
    assert [i.row_id for i in items[:3]] == ["2", "3", "4"]


def test_headers_are_matched_case_insensitively_in_any_order(loader, tmp_path):
    path = _write_xlsx(
        tmp_path / "c.xlsx",
        [[" АРТИКУЛ ", "Наименование", "brand", "Группа"], ["4VB0000", "Трос", "TRW", "Тросы"]],
    )
    [item] = loader.load(path)
    assert (item.raw_article, item.manufacturer, item.product_group) == ("4VB0000", "TRW", "Тросы")


def test_numeric_excel_cells_become_strings(loader, tmp_path):
    path = _write_xlsx(
        tmp_path / "c.xlsx",
        [
            ["Производитель", "Товарная группа", "Артикул"],
            ["X", "Y", 1234567],
            ["X", "Y", 1234567.0],
            ["X", "Y", 12.5],
        ],
    )
    assert [i.raw_article for i in loader.load(path)] == ["1234567", "1234567", "12.5"]


def test_blank_rows_are_skipped_but_line_numbers_kept(loader, tmp_path):
    path = _write_xlsx(
        tmp_path / "c.xlsx",
        [
            ["Производитель", "Товарная группа", "Артикул"],
            ["X", "Y", "A"],
            [None, None, None],
            ["X", "Y", "B"],
        ],
    )
    assert [(i.row_id, i.raw_article) for i in loader.load(path)] == [("2", "A"), ("4", "B")]


def test_short_csv_row_gets_empty_cells(loader, tmp_path):
    path = tmp_path / "c.csv"
    path.write_text("Артикул;Производитель;Товарная группа\n4VB0000\n", encoding="utf-8")
    [item] = loader.load(path)
    assert (item.raw_article, item.manufacturer, item.product_group) == ("4VB0000", "", "")


@pytest.mark.parametrize("delimiter", [";", ",", "\t"])
def test_csv_delimiter_is_detected(loader, tmp_path, delimiter):
    path = tmp_path / "c.csv"
    path.write_text(
        delimiter.join(["Производитель", "Товарная группа", "Артикул"])
        + "\nX"
        + delimiter
        + "Y"
        + delimiter
        + "4VB0000\n",
        encoding="utf-8",
    )
    assert loader.load(path)[0].raw_article == "4VB0000"


def test_cp1251_csv(loader, tmp_path):
    path = tmp_path / "c.csv"
    path.write_bytes("Производитель;Товарная группа;Артикул\nX;Тросы;4VB0000\n".encode("cp1251"))
    assert loader.load(path)[0].product_group == "Тросы"


def test_quoted_multiline_csv_cell_is_one_article(loader, tmp_path):
    path = tmp_path / "c.csv"
    path.write_text('Производитель;Товарная группа;Артикул\nX;Y;"4VB12\n34"\nX;Y;4VB0000\n', encoding="utf-8")
    assert [i.raw_article for i in loader.load(path)] == ["4VB12\n34", "4VB0000"]


def test_missing_columns_are_reported(loader, tmp_path):
    path = _write_xlsx(tmp_path / "c.xlsx", [["Производитель", "Наименование"], ["X", "Y"]])
    with pytest.raises(CatalogFormatError, match="товарная группа, артикул"):
        loader.load(path)


def test_empty_file_is_rejected(loader, tmp_path):
    path = tmp_path / "c.csv"
    path.write_text("", encoding="utf-8")
    with pytest.raises(CatalogFormatError, match="пуст"):
        loader.load(path)


def test_unsupported_format_is_rejected(loader, tmp_path):
    with pytest.raises(CatalogFormatError, match="'.xls'"):
        loader.load(tmp_path / "c.xls")
