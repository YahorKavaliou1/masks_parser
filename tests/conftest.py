import pytest

from masks_parser.domain import Mask
from masks_parser.matching import MaskMatcher, compile_mask
from tests import hilex


@pytest.fixture(scope="session")
def hilex_masks() -> list[Mask]:
    return [compile_mask(m) for m in hilex.MASKS]


@pytest.fixture(scope="session")
def matcher(hilex_masks) -> MaskMatcher:
    return MaskMatcher(hilex_masks)
