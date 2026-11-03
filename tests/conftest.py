import pytest

from masks_parser.catalog import ArticleNormalizer, CatalogLoader
from masks_parser.domain import Certificate, Mask
from masks_parser.matching import MaskMatcher, MismatchExplainer, compile_mask
from tests import hilex


@pytest.fixture(scope="session")
def hilex_masks() -> list[Mask]:
    return [compile_mask(m) for m in hilex.MASKS]


@pytest.fixture(scope="session")
def hilex_certificate(hilex_masks) -> Certificate:
    return Certificate(manufacturer=hilex.MANUFACTURER, product_group=hilex.GROUP, masks=tuple(hilex_masks))


@pytest.fixture(scope="session")
def matcher(hilex_masks) -> MaskMatcher:
    return MaskMatcher(hilex_masks)


@pytest.fixture(scope="session")
def explainer(hilex_masks) -> MismatchExplainer:
    return MismatchExplainer(hilex_masks)


@pytest.fixture(scope="session")
def loader() -> CatalogLoader:
    return CatalogLoader(ArticleNormalizer())
