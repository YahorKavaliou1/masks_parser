import pytest

from masks_parser.domain import CatalogItem, Certificate, MatchStatus
from masks_parser.matching import CatalogChecker, compile_mask
from tests import hilex


def _item(key: str, manufacturer: str = hilex.MANUFACTURER, group: str = hilex.GROUP) -> CatalogItem:
    return CatalogItem(row_id="2", manufacturer=manufacturer, product_group=group, raw_article=key, key=key)


@pytest.fixture(scope="module")
def checker(hilex_certificate) -> CatalogChecker:
    return CatalogChecker(hilex_certificate)


def test_match(checker):
    result = checker.check(_item("4VB0000"))
    assert (result.status, result.mask.pattern, result.reason) == (MatchStatus.MATCH, "4VB****", None)


def test_mask_mismatch_has_reason(checker):
    result = checker.check(_item("4QB0000"))
    assert (result.status, result.mask, result.reason) == (
        MatchStatus.EXCEPTION,
        None,
        "Префикс отсутствует в перечне масок",
    )


def test_scope_is_checked_before_masks(checker):
    # Артикул подходит, но производитель другой — исключение по производителю.
    result = checker.check(_item("4VB0000", manufacturer="TRW"))
    assert (result.status, result.reason) == (MatchStatus.EXCEPTION, "Другой производитель: TRW")


def test_key_matching_several_masks_is_exception():
    # По ТЗ принятый артикул соответствует ровно одной маске; сверка при этом не прерывается.
    certificate = Certificate(
        manufacturer=hilex.MANUFACTURER,
        product_group=hilex.GROUP,
        masks=(compile_mask("4VB****"), compile_mask("4VB0***")),
    )
    checker = CatalogChecker(certificate)
    ambiguous, single = checker.check_all([_item("4VB0123"), _item("4VB1234")])
    assert (ambiguous.status, ambiguous.mask, ambiguous.reason) == (
        MatchStatus.EXCEPTION,
        None,
        "Соответствует нескольким маскам: 4VB****, 4VB0***",
    )
    assert (single.status, single.mask.pattern) == (MatchStatus.MATCH, "4VB****")


def test_check_all_keeps_order(checker):
    keys = ["4VB0000", "bad", "9BB1111"]
    assert [r.item.key for r in checker.check_all(_item(k) for k in keys)] == keys
