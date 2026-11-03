from masks_parser.domain import CatalogItem, Certificate, normalize_name


def _same(a: str, b: str) -> bool:
    return normalize_name(a) == normalize_name(b)


class ScopeChecker:
    """Проверяет, что строка выгрузки относится к производителю и товарной группе сертификата.

    Производитель и группа проверяются отдельными полями, до сопоставления артикула с масками.
    """

    def __init__(self, certificate: Certificate):
        self._certificate = certificate

    def check(self, item: CatalogItem) -> str | None:
        """Возвращает причину исключения или None, если строка в области действия сертификата."""
        if not item.manufacturer.strip():
            return "Производитель не указан"
        if not _same(item.manufacturer, self._certificate.manufacturer):
            return f"Другой производитель: {item.manufacturer.strip()}"
        if not item.product_group.strip():
            return "Товарная группа не указана"
        if not _same(item.product_group, self._certificate.product_group):
            return f"Другая товарная группа: {item.product_group.strip()}"
        return None
