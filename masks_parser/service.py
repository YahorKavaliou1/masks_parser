from pathlib import Path

from masks_parser.catalog import ArticleNormalizer, CatalogFormatError, CatalogLoader
from masks_parser.certificate import CertificateError, CertificateParser
from masks_parser.matching import AmbiguousMatchError, CatalogChecker
from masks_parser.report import ReportSummary, XlsxReportWriter

# Ошибки входных данных: о них сообщается пользователю, а не трейсбеком.
USER_ERRORS = (CertificateError, CatalogFormatError, AmbiguousMatchError, OSError)


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

    def run(self, certificate_path: Path, catalog_path: Path, output_path: Path) -> ReportSummary:
        for path in (certificate_path, catalog_path):
            if not path.is_file():
                raise FileNotFoundError(f"Файл не найден: {path}")

        certificate = self._parser.parse(certificate_path)
        results = CatalogChecker(certificate).check_all(self._loader.load(catalog_path))
        summary = ReportSummary.from_results(certificate, results)
        self._writer.write(summary, results, output_path)
        return summary
