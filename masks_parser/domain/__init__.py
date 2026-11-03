"""Доменные сущности: сертификат, маска, артикул, результат сопоставления."""

from masks_parser.domain.models import CatalogItem, Certificate, Mask, MatchResult, MatchStatus
from masks_parser.domain.names import normalize_name

__all__ = ["CatalogItem", "Certificate", "Mask", "MatchResult", "MatchStatus", "normalize_name"]
