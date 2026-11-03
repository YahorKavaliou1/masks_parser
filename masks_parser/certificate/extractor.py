import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from docx.table import Table


class CertificateError(ValueError):
    """Сертификат не удаётся разобрать или его разделы противоречат друг другу."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("Ошибки в сертификате:\n" + "\n".join(f"- {p}" for p in problems))


@dataclass(frozen=True)
class RegisterRow:
    """Строка рабочего реестра масок как она записана в документе."""

    mask: str
    manufacturer: str = ""
    regex: str = ""


@dataclass(frozen=True)
class CertificateDraft:
    """Всё, что извлечено из документа, до перекрёстной проверки.

    Производитель и группа упоминаются в нескольких местах — собираются все упоминания.
    """

    rows: tuple[RegisterRow, ...]
    manufacturers: tuple[str, ...]
    product_groups: tuple[str, ...]
    listed_masks: tuple[str, ...]  # текстовый перечень «4VB****, 4JB****, …»
    combined_regexes: tuple[str, ...]  # итоговое выражение «^(?:4VB|…)[A-Z0-9]{4}$»
    declared_counts: tuple[int, ...]  # «38 масок», «из 38 префиксов»


_MANUFACTURER = re.compile(r"производитель\s*[–—=-]\s*([^.;]+)", re.IGNORECASE)
_PRODUCT_GROUP = re.compile(r"(?:продукция|товарная группа)\s*[–—=-]\s*([^.;]+)", re.IGNORECASE)
_DECLARED_COUNT = re.compile(r"(\d+)\s+(?:масок|префиксов)", re.IGNORECASE)
_MASK_LIST = re.compile(r"[^\s,]+(?:\s*,\s*[^\s,]+)+")


class DocxCertificateExtractor:
    """Извлекает данные из масочного сертификата .docx формата «правила масок HI-LEX».

    Обязательна таблица реестра с колонкой «Маска»; колонки «Производитель» и «Regex»
    необязательны. Производитель, группа, перечень масок, итоговый regex и заявленное
    число масок ищутся в абзацах текста.
    """

    def extract(self, path: Path) -> CertificateDraft:
        try:
            document = Document(str(path))
        except (PackageNotFoundError, zipfile.BadZipFile, KeyError) as e:
            raise CertificateError([f"Файл не является документом .docx: {path} ({e})"]) from e
        paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
        rows = self._register_rows(document.tables)
        return CertificateDraft(
            rows=rows,
            manufacturers=tuple(r.manufacturer for r in rows if r.manufacturer)
            + self._find_all(_MANUFACTURER, paragraphs),
            product_groups=self._find_all(_PRODUCT_GROUP, paragraphs),
            listed_masks=self._listed_masks(paragraphs),
            combined_regexes=tuple(p for p in paragraphs if p.startswith("^") and p.endswith("$")),
            declared_counts=tuple(int(n) for n in self._find_all(_DECLARED_COUNT, paragraphs)),
        )

    def _register_rows(self, tables: list[Table]) -> tuple[RegisterRow, ...]:
        for table in tables:
            header = [cell.text.strip().casefold() for cell in table.rows[0].cells]
            mask_col = self._column(header, "маска")
            if mask_col is None:
                continue
            manufacturer_col = self._column(header, "производитель")
            regex_col = self._column(header, "regex")
            rows = []
            for row in table.rows[1:]:
                cells = [cell.text.strip() for cell in row.cells]
                if not cells[mask_col]:
                    continue
                rows.append(
                    RegisterRow(
                        mask=cells[mask_col],
                        manufacturer=cells[manufacturer_col] if manufacturer_col is not None else "",
                        regex=cells[regex_col] if regex_col is not None else "",
                    )
                )
            return tuple(rows)
        raise CertificateError(["Не найдена таблица реестра масок (колонка «Маска»)"])

    @staticmethod
    def _column(header: list[str], name: str) -> int | None:
        return next((i for i, title in enumerate(header) if name in title), None)

    @staticmethod
    def _find_all(pattern: re.Pattern[str], paragraphs: list[str]) -> tuple[str, ...]:
        return tuple(m.strip() for p in paragraphs for m in pattern.findall(p))

    @staticmethod
    def _listed_masks(paragraphs: list[str]) -> tuple[str, ...]:
        # Абзац, целиком состоящий из перечня через запятую, где каждый элемент — маска.
        masks = []
        for paragraph in paragraphs:
            text = paragraph.removesuffix(".")
            if _MASK_LIST.fullmatch(text):
                items = [item.strip() for item in text.split(",")]
                if all("*" in item for item in items):
                    masks.extend(items)
        return tuple(masks)
