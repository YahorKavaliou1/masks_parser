from dataclasses import dataclass
from pathlib import Path

from masks_parser.catalog import ArticleNormalizer, CatalogFormatError, CatalogLoader
from masks_parser.certificate import CertificateError, CertificateParser
from masks_parser.domain import MatchResult
from masks_parser.matching import CatalogChecker
from masks_parser.report import ReportSummary, XlsxReportWriter

# Ошибки входных данных: о них сообщается пользователю, а не трейсбеком.
USER_ERRORS = (CertificateError, CatalogFormatError, OSError)


@dataclass(frozen=True)
class Reconciliation:
    """Итог сверки: сводка и результат по каждой строке выгрузки."""

    summary: ReportSummary
    results: list[MatchResult]


class ReportService:
    """Сценарий целиком: сертификат + выгрузка каталога → отчёт сверки."""

    def __init__(
        self,
        parser: CertificateParser | None = None,
        loader: CatalogLoader | None = None,
        writer: XlsxReportWriter | None = None,
    ):
        self._parser = parser or CertificateParser()
        self._loader = loader or CatalogLoader(ArticleNormalizer())
        self._writer = writer or XlsxReportWriter()

    def check(self, certificate_path: Path, catalog_path: Path) -> Reconciliation:
        """Сверка без записи отчёта: нужна, когда результат показывают сразу (веб-интерфейс)."""
        for path in (certificate_path, catalog_path):
            if not path.is_file():
                raise FileNotFoundError(f"Файл не найден: {path}")

        certificate = self._parser.parse(certificate_path)
        results = CatalogChecker(certificate).check_all(self._loader.load(catalog_path))
        return Reconciliation(summary=ReportSummary.from_results(certificate, results), results=results)

    def write(self, reconciliation: Reconciliation, output_path: Path) -> None:
        self._writer.write(reconciliation.summary, reconciliation.results, output_path)

    def run(self, certificate_path: Path, catalog_path: Path, output_path: Path) -> ReportSummary:
        reconciliation = self.check(certificate_path, catalog_path)
        self.write(reconciliation, output_path)
        return reconciliation.summary
