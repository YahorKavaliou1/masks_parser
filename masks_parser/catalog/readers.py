import csv
import io
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Protocol

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException


class CatalogFormatError(ValueError):
    """Файл выгрузки не удаётся прочитать: формат, кодировка или нет нужных колонок."""


class TableReader(Protocol):
    """Читает табличный файл построчно; первая строка — заголовок. Все значения — строки."""

    def rows(self, path: Path) -> Iterator[list[str]]: ...


class CsvTableReader:
    """CSV из UTF-8 (с BOM или без) или Windows-1251; разделитель определяется автоматически."""

    ENCODINGS = ("utf-8-sig", "cp1251")
    DELIMITERS = ";,\t"

    def rows(self, path: Path) -> Iterator[list[str]]:
        text = self._decode(path.read_bytes())
        dialect = self._dialect(text)
        yield from csv.reader(io.StringIO(text, newline=""), dialect)

    def _decode(self, data: bytes) -> str:
        for encoding in self.ENCODINGS:
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise CatalogFormatError(f"Неизвестная кодировка CSV, ожидается одна из: {', '.join(self.ENCODINGS)}")

    def _dialect(self, text: str) -> type[csv.Dialect]:
        header = text.split("\n", 1)[0]
        try:
            return csv.Sniffer().sniff(header, delimiters=self.DELIMITERS)
        except csv.Error:
            return csv.excel


class XlsxTableReader:
    """Первый лист книги Excel. Числовые ячейки приводятся к строке без «.0»."""

    def rows(self, path: Path) -> Iterator[list[str]]:
        try:
            workbook = load_workbook(path, read_only=True, data_only=True)
        except (InvalidFileException, zipfile.BadZipFile, KeyError) as e:
            raise CatalogFormatError(f"Файл не является книгой Excel .xlsx: {path} ({e})") from e
        try:
            for row in workbook.worksheets[0].iter_rows(values_only=True):
                yield [self._to_str(value) for value in row]
        finally:
            workbook.close()

    @staticmethod
    def _to_str(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, float) and value.is_integer():
            # Артикул из одних цифр Excel хранит числом: 1234567.0 → «1234567».
            return str(int(value))
        return str(value)
