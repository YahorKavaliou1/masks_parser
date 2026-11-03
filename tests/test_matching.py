import csv
import random
import re
from pathlib import Path

import pytest

from masks_parser.matching import AmbiguousMatchError, MaskCompiler, MaskMatcher, compile_mask

HILEX_PREFIXES = (
    "4VB 4JB 4AB 9TB 4TB 4HB 9CB 9NB 4GB 4RB 4PB 9VB 4UB 4CB 4NB 4DB 9AB 4FB 4BB "
    "4ZB 9HB 4MB 9DB 9ZB 1PB 5PB 9JB 2HB 5CB 2JB 2PB 9RB 9YB 2KB 9GB 2YB 7HB 9BB"
).split()
HILEX_MASKS = [p + "****" for p in HILEX_PREFIXES]

# Итоговое выражение из раздела «Точное условие машинной проверки» ТЗ.
TZ_REGEX = re.compile(r"^(?:" + "|".join(HILEX_PREFIXES) + r")[A-Z0-9]{4}$")

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


@pytest.fixture(scope="module")
def matcher() -> MaskMatcher:
    return MaskMatcher(compile_mask(m) for m in HILEX_MASKS)


def test_hilex_register_has_38_masks():
    assert len(HILEX_MASKS) == len(set(HILEX_MASKS)) == 38


@pytest.mark.parametrize("prefix", HILEX_PREFIXES)
def test_mask_compiles_to_regex_from_register(prefix):
    # В реестре ТЗ: ^4VB[A-Z0-9]{4}$; якоря не нужны, т.к. используется fullmatch.
    assert compile_mask(prefix + "****").regex.pattern == prefix + "[A-Z0-9]{4}"


# Контрольные примеры из ТЗ.
@pytest.mark.parametrize(
    ("article", "expected_mask"),
    [
        ("4VB0000", "4VB****"),
        ("9BBA1Z9", "9BB****"),
        ("4VB123", None),  # после префикса три символа
        ("4VB12345", None),  # после префикса пять символов
        ("4VB12-3", None),  # дефис внутри артикула
        ("4QB1234", None),  # префикс отсутствует в перечне
        ("4VB12А3", None),  # кириллическая А
    ],
)
def test_tz_control_examples(matcher, article, expected_mask):
    mask = matcher.match(article)
    assert (mask.pattern if mask else None) == expected_mask


@pytest.mark.parametrize(
    "key",
    [
        "4VB0000\n",  # перевод строки в конце: `$` пропустил бы, fullmatch — нет
        "\n4VB0000",
        "4vb0000",  # регистр приводится на этапе нормализации, не в матчере
        "4VB000a",
        " 4VB0000",
        "4VB000０",  # полноширинная цифра 0
        "4VB000٠",  # арабская цифра 0
        "4VB000É",  # латинская буква с диакритикой
        "",
    ],
)
def test_matcher_rejects_non_strict_keys(matcher, key):
    assert matcher.match(key) is None


def test_every_mask_is_reachable(matcher):
    for prefix in HILEX_PREFIXES:
        assert matcher.match(prefix + "Z9O1").pattern == prefix + "****"


def test_matcher_agrees_with_tz_regex(matcher):
    """Набор отдельных масок эквивалентен итоговому выражению из ТЗ."""
    with open(SAMPLES / "catalog_sample.csv", encoding="utf-8-sig", newline="") as f:
        articles = [row["Артикул"] for row in csv.DictReader(f, delimiter=";")]
    rng = random.Random(0)
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-a А"
    articles += [
        rng.choice(HILEX_PREFIXES + ["4QB", "4VA"]) + "".join(rng.choices(alphabet, k=rng.randint(3, 5)))
        for _ in range(5000)
    ]
    for article in articles:
        assert (matcher.match(article) is not None) == (TZ_REGEX.fullmatch(article) is not None), article


def test_literal_regex_chars_are_escaped():
    mask = compile_mask("A.B+**")
    assert mask.matches("A.B+1Z")
    assert not mask.matches("AxBB1Z")


def test_single_wildcard_has_no_quantifier():
    assert compile_mask("A*B**").regex.pattern == "A[A-Z0-9]B[A-Z0-9]{2}"


@pytest.mark.parametrize("pattern", ["", " ", "4VB ****", "4VB****\n"])
def test_invalid_mask_rejected(pattern):
    with pytest.raises(ValueError):
        compile_mask(pattern)


def test_custom_syntax_extends_compiler():
    compiler = MaskCompiler({"*": "[A-Z0-9]", "#": "[0-9]"})
    mask = compiler.compile("AB#*")
    assert mask.regex.pattern == "AB[0-9][A-Z0-9]"
    assert mask.matches("AB1Z")
    assert not mask.matches("ABZZ")
    # «#» в синтаксисе по умолчанию — обычный литерал.
    assert compile_mask("AB#*").matches("AB#Z")


@pytest.mark.parametrize("wildcards", [{}, {"**": "[A-Z]"}, {" ": "[A-Z]"}])
def test_invalid_syntax_rejected(wildcards):
    with pytest.raises(ValueError):
        MaskCompiler(wildcards)


def test_compiler_syntax_is_not_affected_by_caller_dict():
    wildcards = {"*": "[A-Z0-9]"}
    compiler = MaskCompiler(wildcards)
    wildcards["#"] = "[0-9]"
    assert compiler.compile("A#").matches("A#")


def test_duplicate_masks_rejected():
    with pytest.raises(ValueError, match="4VB"):
        MaskMatcher([compile_mask("4VB****"), compile_mask("4VB****")])


def test_overlapping_masks_raise_on_ambiguous_key():
    matcher = MaskMatcher([compile_mask("4VB****"), compile_mask("4VB0***")])
    assert matcher.match("4VB1234").pattern == "4VB****"
    with pytest.raises(AmbiguousMatchError) as exc:
        matcher.match("4VB0123")
    assert [m.pattern for m in exc.value.masks] == ["4VB****", "4VB0***"]
