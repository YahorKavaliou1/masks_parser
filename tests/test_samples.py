"""Сквозная проверка на тестовой выгрузке: область сертификата + нормализация + маски = эталон."""

from masks_parser.matching import CatalogChecker
from tests import hilex


def test_all_sample_rows_match_expected(loader, hilex_certificate):
    expected = {
        str(int(r["row_id"]) + 1): r["expected"] for r in hilex.sample_rows()
    }  # +1 — строка заголовка
    results = CatalogChecker(hilex_certificate).check_all(loader.load(hilex.SAMPLES / "catalog_sample.xlsx"))
    assert len(results) == len(expected) == 214

    for result in results:
        item = result.item
        assert result.status == expected[item.row_id], (item.row_id, item.raw_article, result.reason)
        assert result.reason != "Не соответствует ни одной маске", item.raw_article
