from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from masks_parser.domain import Certificate, MatchResult, MatchStatus


@dataclass(frozen=True)
class ReportSummary:
    """Итоги сверки: сколько строк подошло и сколько артикулов найдено по каждой маске."""

    certificate: Certificate
    total: int
    matched: int
    by_mask: dict[str, int]  # в порядке реестра; маски без находок — с нулём

    @property
    def exceptions(self) -> int:
        return self.total - self.matched

    @classmethod
    def from_results(cls, certificate: Certificate, results: Sequence[MatchResult]) -> "ReportSummary":
        hits = Counter(r.mask.pattern for r in results if r.status is MatchStatus.MATCH)
        return cls(
            certificate=certificate,
            total=len(results),
            matched=sum(hits.values()),
            by_mask={m.pattern: hits[m.pattern] for m in certificate.masks},
        )
