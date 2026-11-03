import pytest

from masks_parser.catalog import ArticleNormalizer


@pytest.fixture(scope="module")
def normalizer() -> ArticleNormalizer:
    return ArticleNormalizer()


@pytest.mark.parametrize(
    ("raw", "key"),
    [
        ("4VB0000", "4VB0000"),
        ("4jb7k2m", "4JB7K2M"),  # латиница в верхний регистр
        ("  4AB1C2D  ", "4AB1C2D"),  # пробелы по краям удаляются
        (" 9TB55AA ", "9TB55AA"),  # NBSP по краям → пробел → удаляется
        (" 4VB0000 ", "4VB0000"),  # узкий и цифровой неразрывные пробелы
        ("4VB 1234", "4VB 1234"),  # NBSP внутри становится обычным пробелом
        ("4VB 1234", "4VB 1234"),  # внутренний пробел остаётся
        ("4VB1234\n", "4VB1234\n"),  # перевод строки не удаляется
        ("\t4VB1234", "\t4VB1234"),  # табуляция — не пробел, остаётся
        ("4vb12а3", "4VB12а3"),  # кириллическая «а» не переводится в верхний регистр
        ("4VB12А3", "4VB12А3"),  # кириллица на латиницу не подменяется
        ("4vb12é4", "4VB12é4"),  # латиница с диакритикой не трогается
        ("2YBoooo", "2YBOOOO"),  # O и 0 остаются разными символами
        ("", ""),
        ("   ", ""),
    ],
)
def test_normalize(normalizer, raw, key):
    assert normalizer.normalize(raw) == key


def test_raw_value_is_not_modified(normalizer):
    raw = " 4vb0000 "
    normalizer.normalize(raw)
    assert raw == " 4vb0000 "
