import string
import unicodedata
from collections.abc import Callable, Iterable

from masks_parser.domain import Mask

_BASE_ALPHABET = frozenset(string.ascii_uppercase + string.digits)


class MismatchExplainer:
    """Объясняет, почему поисковый ключ не подошёл ни под одну маску.

    Вызывается только после неудачного сопоставления: сам ничего не отклоняет,
    а лишь подбирает причину для списка исключений. Правила проверяются по порядку,
    возвращается первая сработавшая причина.
    """

    def __init__(self, masks: Iterable[Mask]):
        self._masks = tuple(masks)
        # Допустимы базовые символы и любые литералы самих масок (например, дефис в чужом формате).
        self._alphabet = _BASE_ALPHABET.union(*(m.pattern for m in self._masks))
        self._rules: tuple[Callable[[str], str | None], ...] = (
            self._empty,
            self._line_break,
            self._inner_space,
            self._cyrillic,
            self._forbidden_char,
            self._unknown_prefix,
            self._wrong_length,
        )

    def explain(self, key: str) -> str:
        for rule in self._rules:
            reason = rule(key)
            if reason:
                return reason
        return "Не соответствует ни одной маске"

    @staticmethod
    def _empty(key: str) -> str | None:
        return "Пустой артикул" if not key else None

    @staticmethod
    def _line_break(key: str) -> str | None:
        return "Перевод строки в артикуле" if "\n" in key or "\r" in key else None

    @staticmethod
    def _inner_space(key: str) -> str | None:
        return "Пробел внутри артикула" if any(ch.isspace() for ch in key) else None

    @staticmethod
    def _cyrillic(key: str) -> str | None:
        for pos, ch in enumerate(key, start=1):
            if unicodedata.name(ch, "").startswith("CYRILLIC"):
                return f"Кириллическая буква «{ch}» в позиции {pos}"
        return None

    def _forbidden_char(self, key: str) -> str | None:
        for pos, ch in enumerate(key, start=1):
            if ch not in self._alphabet:
                return f"Недопустимый символ «{ch}» в позиции {pos}"
        return None

    def _unknown_prefix(self, key: str) -> str | None:
        if any(key.startswith(m.prefix) for m in self._masks):
            return None
        return "Префикс отсутствует в перечне масок"

    def _wrong_length(self, key: str) -> str | None:
        candidates = [m for m in self._masks if key.startswith(m.prefix)]
        if any(m.length == len(key) for m in candidates):
            return None
        expected = ", ".join(f"{m.pattern} — {m.length}" for m in candidates)
        return f"Длина {len(key)} символов, ожидается: {expected}"
