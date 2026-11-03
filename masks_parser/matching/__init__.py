"""Компиляция масок в regex и сопоставление артикулов."""

from masks_parser.matching.explainer import MismatchExplainer
from masks_parser.matching.mask import DEFAULT_WILDCARDS, MaskCompiler, compile_mask
from masks_parser.matching.matcher import AmbiguousMatchError, MaskMatcher

__all__ = [
    "DEFAULT_WILDCARDS",
    "AmbiguousMatchError",
    "MaskCompiler",
    "MaskMatcher",
    "MismatchExplainer",
    "compile_mask",
]
