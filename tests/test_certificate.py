from pathlib import Path

import pytest
from docx import Document

from masks_parser.certificate import (
    CertificateDraft,
    CertificateError,
    CertificateParser,
    CertificateValidator,
    RegisterRow,
)
from masks_parser.matching import compile_mask
from scripts.make_sample_certificate import build_certificate
from tests import hilex


@pytest.fixture(scope="module")
def parser() -> CertificateParser:
    return CertificateParser()


def _problems(parser: CertificateParser, path: Path) -> list[str]:
    with pytest.raises(CertificateError) as exc:
        parser.parse(path)
    return exc.value.problems


def test_sample_certificate_is_parsed(parser, hilex_certificate):
    certificate = parser.parse(hilex.SAMPLES / "certificate_sample.docx")
    assert certificate == hilex_certificate
    assert [m.pattern for m in certificate.masks] == hilex.MASKS


def test_consistent_generated_certificate_is_parsed(parser, tmp_path):
    certificate = parser.parse(build_certificate(tmp_path / "c.docx", masks=["AB**", "CD**"]))
    assert [m.pattern for m in certificate.masks] == ["AB**", "CD**"]


def test_group_mentions_differing_only_in_case_are_consistent(parser, tmp_path):
    path = build_certificate(tmp_path / "c.docx")
    _replace_paragraph(
        path,
        "Условие отбора:",
        f"Условие отбора: производитель = {hilex.MANUFACTURER}; товарная группа = тросы стояночного тормоза.",
    )
    assert parser.parse(path).product_group == hilex.GROUP


@pytest.mark.parametrize(
    ("kwargs", "problem"),
    [
        ({"listed": hilex.MASKS[:-1]}, "Перечень масок в тексте: нет масок из реестра: 9BB****"),
        (
            {"listed": [*hilex.MASKS, "4QB****"]},
            "Перечень масок в тексте: лишние маски, которых нет в реестре: 4QB****",
        ),
        (
            {"combined": "^(?:" + "|".join(hilex.PREFIXES[1:]) + ")[A-Z0-9]{4}$"},
            "Итоговое выражение: нет масок из реестра: 4VB[A-Z0-9]{4}",
        ),
        (
            {"combined": "^(?:" + "|".join(hilex.PREFIXES) + ")[A-Z0-9]{5}$"},
            "Итоговое выражение: нет масок из реестра",
        ),
        ({"combined": "^4VB.*$"}, "Итоговое выражение не удалось разобрать: ^4VB.*$"),
        ({"declared": 39}, "В тексте заявлено 39 масок, в реестре 38"),
        (
            {"row_regex": {"4JB****": "^4JB[A-Z0-9]{5}$"}},
            "Regex ^4JB[A-Z0-9]{5}$ в реестре не совпадает с маской 4JB**** (ожидается ^4JB[A-Z0-9]{4}$)",
        ),
        ({"masks": ["AB**", "AB**"]}, "Маски повторяются в реестре: AB**"),
        ({"masks": ["AB **"], "listed": ["AB**"]}, "Некорректная маска: 'AB **'"),
        ({"with_table": False}, "Не найдена таблица реестра масок (колонка «Маска»)"),
    ],
)
def test_inconsistent_certificate_is_rejected(parser, tmp_path, kwargs, problem):
    problems = _problems(parser, build_certificate(tmp_path / "c.docx", **kwargs))
    assert any(p.startswith(problem) for p in problems), problems


def test_manufacturer_mismatch_between_sections(parser, tmp_path):
    path = build_certificate(tmp_path / "c.docx")
    _replace_paragraph(path, "Производитель –", f"Производитель – HI-LEX LTD. Продукция – {hilex.GROUP}.")
    assert _problems(parser, path) == ["Разные значения поля «производитель»: HI-LEX CORPORATION, HI-LEX LTD"]


def test_all_problems_are_reported_together(parser, tmp_path):
    path = build_certificate(tmp_path / "c.docx", declared=40, listed=hilex.MASKS[:-1])
    assert len(_problems(parser, path)) == 2


def test_optional_sections_may_be_absent():
    masks = [compile_mask("AB**")]
    draft = CertificateDraft(
        rows=(RegisterRow(mask="AB**"),),
        manufacturers=("X",),
        product_groups=("Y",),
        listed_masks=(),
        combined_regexes=(),
        declared_counts=(),
    )
    assert CertificateValidator().validate(draft, masks) == []


def test_missing_manufacturer_and_group_are_reported():
    draft = CertificateDraft(
        rows=(RegisterRow(mask="AB**"),),
        manufacturers=(),
        product_groups=(),
        listed_masks=(),
        combined_regexes=(),
        declared_counts=(),
    )
    assert CertificateValidator().validate(draft, [compile_mask("AB**")]) == [
        "Не указан(а) производитель",
        "Не указан(а) товарная группа",
    ]


def _replace_paragraph(path: Path, startswith: str, text: str) -> None:
    doc = Document(str(path))
    paragraph = next(p for p in doc.paragraphs if p.text.startswith(startswith))
    paragraph.text = text
    doc.save(str(path))
