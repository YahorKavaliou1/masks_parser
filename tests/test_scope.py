import pytest

from masks_parser.domain import CatalogItem
from masks_parser.matching import ScopeChecker
from tests import hilex


def _item(manufacturer: str, product_group: str) -> CatalogItem:
    return CatalogItem(
        row_id="2", manufacturer=manufacturer, product_group=product_group, raw_article="", key=""
    )


@pytest.mark.parametrize(
    ("manufacturer", "product_group", "reason"),
    [
        (hilex.MANUFACTURER, hilex.GROUP, None),
        ("Hi-Lex Corporation ", hilex.GROUP, None),  # без учёта регистра и краевых пробелов
        (hilex.MANUFACTURER, " тросы стояночного тормоза", None),
        ("TRW", hilex.GROUP, "Другой производитель: TRW"),
        ("HILEX CORPORATION", hilex.GROUP, "Другой производитель: HILEX CORPORATION"),
        ("", hilex.GROUP, "Производитель не указан"),
        ("  ", hilex.GROUP, "Производитель не указан"),
        (hilex.MANUFACTURER, "Тросы сцепления", "Другая товарная группа: Тросы сцепления"),
        (hilex.MANUFACTURER, "", "Товарная группа не указана"),
        ("TRW", "", "Другой производитель: TRW"),  # производитель проверяется первым
    ],
)
def test_check(hilex_certificate, manufacturer, product_group, reason):
    assert ScopeChecker(hilex_certificate).check(_item(manufacturer, product_group)) == reason
