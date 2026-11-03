import re
from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True)
class Mask:
    """Маска артикула: человекочитаемая запись и regex для полного сопоставления.

    Каждый символ маски соответствует ровно одному символу артикула,
    поэтому длина артикула равна длине маски.
    """

    pattern: str
    regex: re.Pattern[str]
    prefix: str  # неизменная часть до первой подстановки

    @property
    def length(self) -> int:
        return len(self.pattern)

    def matches(self, key: str) -> bool:
        return self.regex.fullmatch(key) is not None


@dataclass(frozen=True)
class Certificate:
    manufacturer: str
    product_group: str
    masks: tuple[Mask, ...]


@dataclass(frozen=True)
class CatalogItem:
    """Строка выгрузки: исходный артикул хранится без изменений, сопоставляется поисковый ключ."""

    row_id: str
    manufacturer: str
    product_group: str
    raw_article: str
    key: str


class MatchStatus(StrEnum):
    MATCH = "Соответствует"
    EXCEPTION = "Исключение"


@dataclass(frozen=True)
class MatchResult:
    item: CatalogItem
    status: MatchStatus
    mask: Mask | None = None
    reason: str | None = None
