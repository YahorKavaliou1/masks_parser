from collections.abc import Iterable

from masks_parser.domain import CatalogItem, Certificate, MatchResult, MatchStatus
from masks_parser.matching.explainer import MismatchExplainer
from masks_parser.matching.matcher import MaskMatcher
from masks_parser.matching.scope import ScopeChecker


class CatalogChecker:
    """Проверяет строки выгрузки по сертификату: область действия → маски → причина исключения."""

    def __init__(self, certificate: Certificate):
        self._scope = ScopeChecker(certificate)
        self._matcher = MaskMatcher(certificate.masks)
        self._explainer = MismatchExplainer(certificate.masks)

    def check(self, item: CatalogItem) -> MatchResult:
        if reason := self._scope.check(item):
            return MatchResult(item=item, status=MatchStatus.EXCEPTION, reason=reason)
        if mask := self._matcher.match(item.key):
            return MatchResult(item=item, status=MatchStatus.MATCH, mask=mask)
        return MatchResult(item=item, status=MatchStatus.EXCEPTION, reason=self._explainer.explain(item.key))

    def check_all(self, items: Iterable[CatalogItem]) -> list[MatchResult]:
        return [self.check(item) for item in items]
