import string

_LATIN_UPPER = str.maketrans(string.ascii_lowercase, string.ascii_uppercase)
_NBSP_TO_SPACE = str.maketrans({" ": " ", " ": " ", " ": " "})


class ArticleNormalizer:
    """Строит поисковый ключ артикула по правилам нормализации выгрузки из ТЗ.

    - латинские a–z переводятся в верхний регистр (кириллица и прочие буквы не трогаются);
    - неразрывные пробелы заменяются обычными;
    - удаляются только обычные пробелы по краям.

    Всё остальное (внутренние пробелы, переводы строк, точки, дефисы, кириллица)
    остаётся в ключе как есть и отсеивается на сопоставлении с масками.
    """

    def normalize(self, raw: str) -> str:
        return raw.translate(_NBSP_TO_SPACE).strip(" ").translate(_LATIN_UPPER)
