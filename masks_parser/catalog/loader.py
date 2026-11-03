from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from masks_parser.catalog.normalizer import ArticleNormalizer
from masks_parser.catalog.readers import CatalogFormatError, CsvTableReader, TableReader, XlsxTableReader
from masks_parser.domain import CatalogItem


@dataclass(frozen=True)
class CatalogColumns:
    """Допустимые названия колонок выгрузки (без учёта регистра и краевых пробелов)."""

    manufacturer: tuple[str, ...] = ("производитель", "manufacturer", "бренд", "brand")
    product_group: tuple[str, ...] = ("товарная группа", "группа", "product group")
    article: tuple[str, ...] = ("артикул", "article", "sku")

    def resolve(self, header: list[str]) -> dict[str, int]:
        """Возвращает индексы колонок по их роли: manufacturer, product_group, article."""
        names = [h.strip().casefold() for h in header]
        indexes, missing = {}, []
        for role, aliases in vars(self).items():
            index = next((i for i, name in enumerate(names) if name in aliases), None)
            if index is None:
                missing.append(aliases[0])
            else:
                indexes[role] = index
        if missing:
            raise CatalogFormatError(
                f"В выгрузке нет колонок: {', '.join(missing)}. Найдены: {', '.join(header) or '—'}"
            )
        return indexes


DEFAULT_COLUMNS = CatalogColumns()
DEFAULT_READERS: Mapping[str, TableReader] = MappingProxyType(
    {".csv": CsvTableReader(), ".xlsx": XlsxTableReader()}
)


class CatalogLoader:
    """Загружает выгрузку каталога в CatalogItem: исходный артикул + поисковый ключ.

    `row_id` — номер строки в файле (заголовок — строка 1), чтобы исключение было легко найти.
    Полностью пустые строки пропускаются.
    """

    def __init__(
        self,
        normalizer: ArticleNormalizer,
        columns: CatalogColumns = DEFAULT_COLUMNS,
        readers: Mapping[str, TableReader] = DEFAULT_READERS,
    ):
        self._normalizer = normalizer
        self._columns = columns
        self._readers = readers

    def load(self, path: Path) -> list[CatalogItem]:
        rows = self._reader_for(path).rows(path)
        header = next(rows, None)
        if header is None:
            raise CatalogFormatError(f"Файл выгрузки пуст: {path}")
        index = self._columns.resolve(header)

        items = []
        for line, row in enumerate(rows, start=2):
            if not any(cell.strip() for cell in row):
                continue
            raw_article = self._cell(row, index["article"])
            items.append(
                CatalogItem(
                    row_id=str(line),
                    manufacturer=self._cell(row, index["manufacturer"]),
                    product_group=self._cell(row, index["product_group"]),
                    raw_article=raw_article,
                    key=self._normalizer.normalize(raw_article),
                )
            )
        return items

    def _reader_for(self, path: Path) -> TableReader:
        try:
            return self._readers[path.suffix.lower()]
        except KeyError:
            supported = ", ".join(self._readers)
            raise CatalogFormatError(
                f"Неподдерживаемый формат {path.suffix!r}, ожидается: {supported}"
            ) from None

    @staticmethod
    def _cell(row: list[str], index: int) -> str:
        # Короткие строки CSV и обрезанные строки Excel: недостающие ячейки — пустые.
        return row[index] if index < len(row) else ""
