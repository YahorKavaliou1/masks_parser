"""Сквозная проверка на тестовой выгрузке: область сертификата + нормализация + маски = эталон."""

from masks_parser.domain import MatchStatus
from masks_parser.matching import ScopeChecker
from tests import hilex


def test_all_sample_rows_match_expected(loader, hilex_certificate, matcher, explainer):
    scope = ScopeChecker(hilex_certificate)
    expected = {
        str(int(r["row_id"]) + 1): r["expected"] for r in hilex.sample_rows()
    }  # +1 — строка заголовка
    items = loader.load(hilex.SAMPLES / "catalog_sample.xlsx")
    assert len(items) == len(expected) == 214

    for item in items:
        reason = scope.check(item)
        mask = None if reason else matcher.match(item.key)
        if not reason and not mask:
            reason = explainer.explain(item.key)
            assert reason != "Не соответствует ни одной маске", item.raw_article
        status = MatchStatus.MATCH if mask else MatchStatus.EXCEPTION
        assert status == expected[item.row_id], (item.row_id, item.raw_article, reason)
