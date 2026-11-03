from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet

from masks_parser.domain import MatchResult, MatchStatus
from masks_parser.report.summary import ReportSummary

_BOLD = Font(bold=True)


@dataclass(frozen=True)
class Column:
    title: str
    width: int
    value: Callable[[MatchResult], object]


MATCH_COLUMNS = (
    Column("Строка", 8, lambda r: int(r.item.row_id)),
    Column("Производитель", 24, lambda r: r.item.manufacturer),
    Column("Товарная группа", 28, lambda r: r.item.product_group),
    Column("Артикул", 16, lambda r: r.item.raw_article),
    Column("Поисковый ключ", 16, lambda r: r.item.key),
    Column("Маска", 12, lambda r: r.mask.pattern),
)

EXCEPTION_COLUMNS = (
    Column("Строка", 8, lambda r: int(r.item.row_id)),
    Column("Производитель", 24, lambda r: r.item.manufacturer),
    Column("Товарная группа", 28, lambda r: r.item.product_group),
    Column("Артикул", 16, lambda r: r.item.raw_article),
    Column("Причина", 60, lambda r: r.reason),
)


class XlsxReportWriter:
    """Пишет отчёт сверки в .xlsx: листы «Соответствует», «Исключения», «Сводка».

    Артикулы записываются строго как текст: строка «=1+1» не становится формулой,
    а управляющие символы, недопустимые в xlsx, заменяются на видимые «\\xNN».
    """

    def write(self, summary: ReportSummary, results: Sequence[MatchResult], path: Path) -> None:
        workbook = Workbook()
        matches = [r for r in results if r.status is MatchStatus.MATCH]
        exceptions = [r for r in results if r.status is MatchStatus.EXCEPTION]

        self._write_table(workbook.active, "Соответствует", MATCH_COLUMNS, matches)
        self._write_table(workbook.create_sheet(), "Исключения", EXCEPTION_COLUMNS, exceptions)
        self._write_summary(workbook.create_sheet("Сводка"), summary)

        path.parent.mkdir(parents=True, exist_ok=True)
        workbook.save(path)

    def _write_table(
        self, sheet: Worksheet, title: str, columns: Sequence[Column], results: Iterable[MatchResult]
    ) -> None:
        sheet.title = title
        self._append(sheet, [c.title for c in columns], bold=True)
        for result in results:
            self._append(sheet, [c.value(result) for c in columns])
        for index, column in enumerate(columns, start=1):
            sheet.column_dimensions[sheet.cell(1, index).column_letter].width = column.width
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions

    def _write_summary(self, sheet: Worksheet, summary: ReportSummary) -> None:
        certificate = summary.certificate
        for label, value in (
            ("Производитель", certificate.manufacturer),
            ("Товарная группа", certificate.product_group),
            ("Масок в сертификате", len(certificate.masks)),
            ("Строк в выгрузке", summary.total),
            ("Соответствует", summary.matched),
            ("Исключений", summary.exceptions),
        ):
            self._append(sheet, [label, value])
            sheet.cell(sheet.max_row, 1).font = _BOLD
        sheet.append([])
        self._append(sheet, ["Маска", "Найдено артикулов"], bold=True)
        for pattern, count in summary.by_mask.items():
            self._append(sheet, [pattern, count])
        sheet.column_dimensions["A"].width = 24
        sheet.column_dimensions["B"].width = 28

    @staticmethod
    def _append(sheet: Worksheet, values: Sequence[object], bold: bool = False) -> None:
        sheet.append([_safe(v) for v in values])
        for cell in sheet[sheet.max_row]:
            if isinstance(cell.value, str):
                cell.data_type = "s"  # иначе строка, начинающаяся с «=», станет формулой
            if bold:
                cell.font = _BOLD


def _safe(value: object) -> object:
    if isinstance(value, str):
        return ILLEGAL_CHARACTERS_RE.sub(lambda m: f"\\x{ord(m.group()):02X}", value)
    return value
