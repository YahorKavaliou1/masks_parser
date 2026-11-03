import re
from collections import Counter

from masks_parser.certificate.extractor import CertificateDraft
from masks_parser.domain import Mask, normalize_name

_COMBINED = re.compile(r"\^\(\?:(?P<prefixes>[^()]+)\)(?P<tail>.+)\$")


class CertificateValidator:
    """Перекрёстная проверка разделов сертификата: реестр, перечень, итоговый regex, число масок.

    Необязательный раздел (перечень, regex, число) проверяется, только если он найден в документе;
    если найден — обязан совпадать с реестром. Возвращает список всех найденных расхождений.
    """

    def validate(self, draft: CertificateDraft, masks: list[Mask]) -> list[str]:
        patterns = [m.pattern for m in masks]
        return [
            *self._names("производитель", draft.manufacturers),
            *self._names("товарная группа", draft.product_groups),
            *self._duplicates(patterns),
            *self._row_regexes(draft, masks),
            *self._listed(draft.listed_masks, patterns),
            *self._combined(draft.combined_regexes, masks),
            *self._counts(draft.declared_counts, len(masks)),
        ]

    @staticmethod
    def _names(what: str, mentions: tuple[str, ...]) -> list[str]:
        if not mentions:
            return [f"Не указан(а) {what}"]
        if len({normalize_name(m) for m in mentions}) > 1:
            return [f"Разные значения поля «{what}»: {', '.join(dict.fromkeys(mentions))}"]
        return []

    @staticmethod
    def _duplicates(patterns: list[str]) -> list[str]:
        repeated = [p for p, n in Counter(patterns).items() if n > 1]
        return [f"Маски повторяются в реестре: {', '.join(repeated)}"] if repeated else []

    @staticmethod
    def _row_regexes(draft: CertificateDraft, masks: list[Mask]) -> list[str]:
        return [
            f"Regex {row.regex} в реестре не совпадает с маской {mask.pattern} "
            f"(ожидается ^{mask.regex.pattern}$)"
            for row, mask in zip(draft.rows, masks, strict=True)
            if row.regex and row.regex.removeprefix("^").removesuffix("$") != mask.regex.pattern
        ]

    @staticmethod
    def _listed(listed: tuple[str, ...], patterns: list[str]) -> list[str]:
        if not listed:
            return []
        return _set_diff("Перечень масок в тексте", set(listed), set(patterns))

    @staticmethod
    def _combined(regexes: tuple[str, ...], masks: list[Mask]) -> list[str]:
        expected = {m.regex.pattern for m in masks}
        problems = []
        for regex in regexes:
            parsed = _COMBINED.fullmatch(regex)
            if not parsed:
                problems.append(f"Итоговое выражение не удалось разобрать: {regex}")
                continue
            actual = {prefix + parsed["tail"] for prefix in parsed["prefixes"].split("|")}
            problems += _set_diff("Итоговое выражение", actual, expected)
        return problems

    @staticmethod
    def _counts(declared: tuple[int, ...], actual: int) -> list[str]:
        wrong = sorted({n for n in declared if n != actual})
        return [f"В тексте заявлено {n} масок, в реестре {actual}" for n in wrong]


def _set_diff(section: str, actual: set[str], expected: set[str]) -> list[str]:
    problems = []
    if missing := sorted(expected - actual):
        problems.append(f"{section}: нет масок из реестра: {', '.join(missing)}")
    if extra := sorted(actual - expected):
        problems.append(f"{section}: лишние маски, которых нет в реестре: {', '.join(extra)}")
    return problems
