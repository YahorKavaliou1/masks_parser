"""Сквозные тесты командной строки: файлы из samples/ → отчёт, сверенный с эталоном."""

import subprocess
import sys

import pytest
from openpyxl import load_workbook

from masks_parser.cli import main
from scripts.make_sample_certificate import build_certificate
from tests import hilex

CERTIFICATE = str(hilex.SAMPLES / "certificate_sample.docx")
CATALOG = str(hilex.SAMPLES / "catalog_sample.xlsx")


def _run(capsys, *args: str) -> tuple[int, str, str]:
    code = main(list(args))
    out, err = capsys.readouterr()
    return code, out, err


def _row_ids(sheet) -> set[int]:
    return {row[0] for row in sheet.iter_rows(min_row=2, values_only=True)}


@pytest.mark.parametrize("catalog", [CATALOG, str(hilex.SAMPLES / "catalog_sample.csv")])
def test_report_matches_expected(capsys, tmp_path, catalog):
    output = tmp_path / "report.xlsx"
    code, out, err = _run(capsys, "--certificate", CERTIFICATE, "--catalog", catalog, "--output", str(output))
    assert (code, err) == (0, "")
    assert out.splitlines() == [
        f"Сертификат: {hilex.MANUFACTURER} / {hilex.GROUP}, масок: 38",
        "Строк в выгрузке: 214",
        "Соответствует: 123",
        "Исключений: 91",
        f"Отчёт: {output}",
    ]

    # Эталон нумерует строки данных с 1, отчёт — строками файла (заголовок — строка 1).
    expected = {r["expected"]: set() for r in hilex.sample_rows()}
    for r in hilex.sample_rows():
        expected[r["expected"]].add(int(r["row_id"]) + 1)
    workbook = load_workbook(output)
    assert _row_ids(workbook["Соответствует"]) == expected["Соответствует"]
    assert _row_ids(workbook["Исключения"]) == expected["Исключение"]


def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "masks-parser" in capsys.readouterr().out


def test_required_arguments(capsys):
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2
    assert "--certificate" in capsys.readouterr().err


def test_missing_file(capsys, tmp_path):
    code, out, err = _run(capsys, "--certificate", str(tmp_path / "nope.docx"), "--catalog", CATALOG)
    assert (code, out) == (1, "")
    assert err == f"Ошибка: Файл не найден: {tmp_path / 'nope.docx'}\n"


def test_broken_docx(capsys, tmp_path):
    broken = tmp_path / "c.docx"
    broken.write_text("not a docx")
    code, _, err = _run(capsys, "--certificate", str(broken), "--catalog", CATALOG)
    assert code == 1
    assert "Файл не является документом .docx" in err


def test_broken_xlsx(capsys, tmp_path):
    broken = tmp_path / "c.xlsx"
    broken.write_text("not an xlsx")
    code, _, err = _run(capsys, "--certificate", CERTIFICATE, "--catalog", str(broken))
    assert code == 1
    assert "Файл не является книгой Excel .xlsx" in err


def test_inconsistent_certificate_lists_problems(capsys, tmp_path):
    certificate = build_certificate(tmp_path / "c.docx", declared=39)
    output = tmp_path / "report.xlsx"
    code, _, err = _run(
        capsys, "--certificate", str(certificate), "--catalog", CATALOG, "--output", str(output)
    )
    assert code == 1
    assert "- В тексте заявлено 39 масок, в реестре 38" in err
    assert not output.exists()


def test_missing_catalog_columns(capsys, tmp_path):
    catalog = tmp_path / "c.csv"
    catalog.write_text("Артикул\n4VB0000\n", encoding="utf-8")
    code, _, err = _run(capsys, "--certificate", CERTIFICATE, "--catalog", str(catalog))
    assert code == 1
    assert "В выгрузке нет колонок: производитель, товарная группа" in err


def test_module_entry_point():
    result = subprocess.run(
        [sys.executable, "-m", "masks_parser", "--version"], capture_output=True, text=True, check=False
    )
    assert (result.returncode, result.stdout.startswith("masks-parser")) == (0, True)
