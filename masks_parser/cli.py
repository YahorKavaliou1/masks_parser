"""Точка входа командной строки."""

import argparse
import sys
from pathlib import Path

from masks_parser import __version__
from masks_parser.report import ReportSummary
from masks_parser.service import USER_ERRORS, ReportService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="masks-parser",
        description="Сверка выгрузки каталога с масками артикулов из сертификата.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--certificate", type=Path, required=True, help="масочный сертификат (.docx)")
    parser.add_argument("--catalog", type=Path, required=True, help="выгрузка каталога (.csv / .xlsx)")
    parser.add_argument("--output", type=Path, default=Path("data/output/report.xlsx"), help="путь к отчёту")
    return parser


def format_summary(summary: ReportSummary, output: Path) -> str:
    certificate = summary.certificate
    return "\n".join(
        [
            f"Сертификат: {certificate.manufacturer} / {certificate.product_group}, "
            f"масок: {len(certificate.masks)}",
            f"Строк в выгрузке: {summary.total}",
            f"Соответствует: {summary.matched}",
            f"Исключений: {summary.exceptions}",
            f"Отчёт: {output}",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = ReportService().run(args.certificate, args.catalog, args.output)
    except USER_ERRORS as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 1
    print(format_summary(summary, args.output))
    return 0
