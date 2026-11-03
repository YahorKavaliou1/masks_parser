import unicodedata


def normalize_name(name: str) -> str:
    """Ключ сравнения названий производителя и товарной группы: без регистра и краевых пробелов."""
    return name.strip().casefold()


def is_cyrillic(ch: str) -> bool:
    return unicodedata.name(ch, "").startswith("CYRILLIC")


def show_char(ch: str) -> str:
    """Символ для сообщения: невидимые (табуляция, пробел нулевой ширины, управляющие) — как U+XXXX."""
    return ch if ch.isprintable() and not ch.isspace() else f"U+{ord(ch):04X}"
