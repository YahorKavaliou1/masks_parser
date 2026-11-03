"""Компиляция масок в regex и сопоставление артикулов."""

from masks_parser.matching.checker import CatalogChecker
from masks_parser.matching.explainer import MismatchExplainer
from masks_parser.matching.mask import DEFAULT_WILDCARDS, MaskCompiler, compile_mask
from masks_parser.matching.matcher import AmbiguousMatchError, MaskMatcher
from masks_parser.matching.scope import ScopeChecker

__all__ = [
    "DEFAULT_WILDCARDS",
    "AmbiguousMatchError",
    "CatalogChecker",
    "MaskCompiler",
    "MaskMatcher",
    "MismatchExplainer",
    "ScopeChecker",
    "compile_mask",
]
