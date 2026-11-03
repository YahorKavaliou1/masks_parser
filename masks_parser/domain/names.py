def normalize_name(name: str) -> str:
    """Ключ сравнения названий производителя и товарной группы: без регистра и краевых пробелов."""
    return name.strip().casefold()
