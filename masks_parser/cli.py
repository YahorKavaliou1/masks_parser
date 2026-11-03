"""Точка входа командной строки. Пока только каркас аргументов."""

import argparse
from pathlib import Path

from masks_parser import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="masks-parser",
        description="Сверка выгрузки каталога с масками артикулов из сертификата.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--certificate", type=Path, help="масочный сертификат (.docx)")
    parser.add_argument("--catalog", type=Path, help="выгрузка каталога (.csv / .xlsx)")
    parser.add_argument("--output", type=Path, default=Path("data/output/report.xlsx"), help="путь к отчёту")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not (args.certificate and args.catalog):
        build_parser().print_help()
        return 0
    raise NotImplementedError("Сопоставление ещё не реализовано")
