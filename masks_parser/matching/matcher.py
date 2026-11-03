from collections.abc import Iterable

from masks_parser.domain import Mask


class AmbiguousMatchError(ValueError):
    """Артикул подходит под несколько масок: перечень масок сертификата пересекается."""

    def __init__(self, key: str, masks: list[Mask]):
        self.key = key
        self.masks = masks
        patterns = ", ".join(m.pattern for m in masks)
        super().__init__(f"Артикул {key!r} соответствует нескольким маскам: {patterns}")


class MaskMatcher:
    """Сопоставляет поисковый ключ артикула с перечнем масок сертификата."""

    def __init__(self, masks: Iterable[Mask]):
        self.masks = tuple(masks)
        patterns = [m.pattern for m in self.masks]
        duplicates = sorted({p for p in patterns if patterns.count(p) > 1})
        if duplicates:
            raise ValueError(f"Маски повторяются: {', '.join(duplicates)}")

    def match(self, key: str) -> Mask | None:
        """Возвращает единственную подходящую маску или None.

        Ключ должен быть уже нормализован: регистр и пробелы здесь не обрабатываются.
        """
        found = [m for m in self.masks if m.matches(key)]
        if len(found) > 1:
            raise AmbiguousMatchError(key, found)
        return found[0] if found else None
