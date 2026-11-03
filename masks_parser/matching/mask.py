import re
from collections.abc import Mapping
from itertools import groupby
from types import MappingProxyType

from masks_parser.domain import Mask

# Синтаксис масок HI-LEX: «*» — одна цифра 0–9 или заглавная латинская буква A–Z.
DEFAULT_WILDCARDS: Mapping[str, str] = MappingProxyType({"*": "[A-Z0-9]"})


class MaskCompiler:
    """Компилирует маску вида `4VB****` в regex `4VB[A-Z0-9]{4}`.

    Синтаксис задаётся словарём «символ-подстановка → класс символов regex»;
    остальные символы маски считаются литералами. Сопоставление выполняется
    через fullmatch, поэтому якоря ^ и $ не нужны, а перевод строки в конце
    артикула не проходит (в отличие от `$`).
    """

    def __init__(self, wildcards: Mapping[str, str] = DEFAULT_WILDCARDS):
        if not wildcards or any(len(ch) != 1 or ch.isspace() for ch in wildcards):
            raise ValueError(f"Некорректный синтаксис масок: {dict(wildcards)!r}")
        self._wildcards = MappingProxyType(dict(wildcards))

    def compile(self, pattern: str) -> Mask:
        if not pattern or any(ch.isspace() for ch in pattern):
            raise ValueError(f"Некорректная маска: {pattern!r}")
        regex = "".join(self._compile_run(ch, len(list(run))) for ch, run in groupby(pattern))
        return Mask(pattern=pattern, regex=re.compile(regex), prefix=self._prefix(pattern))

    def _prefix(self, pattern: str) -> str:
        for i, ch in enumerate(pattern):
            if ch in self._wildcards:
                return pattern[:i]
        return pattern

    def _compile_run(self, ch: str, count: int) -> str:
        if ch not in self._wildcards:
            return re.escape(ch) * count
        return self._wildcards[ch] + (f"{{{count}}}" if count > 1 else "")


compile_mask = MaskCompiler().compile
