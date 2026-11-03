"""Доменные сущности: сертификат, маска, артикул, результат сопоставления."""

from masks_parser.domain.models import CatalogItem, Certificate, Mask, MatchResult, MatchStatus

__all__ = ["CatalogItem", "Certificate", "Mask", "MatchResult", "MatchStatus"]
