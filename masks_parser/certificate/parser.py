from pathlib import Path

from masks_parser.certificate.extractor import CertificateError, DocxCertificateExtractor
from masks_parser.certificate.validator import CertificateValidator
from masks_parser.domain import Certificate, Mask
from masks_parser.matching import MaskCompiler


class CertificateParser:
    """Сертификат .docx → проверенный Certificate: извлечь, скомпилировать маски, сверить разделы.

    При любом расхождении бросает CertificateError со списком всех проблем,
    чтобы неверный сертификат не дал «тихо» неполный результат.
    """

    def __init__(
        self,
        extractor: DocxCertificateExtractor | None = None,
        compiler: MaskCompiler | None = None,
        validator: CertificateValidator | None = None,
    ):
        self._extractor = extractor or DocxCertificateExtractor()
        self._compiler = compiler or MaskCompiler()
        self._validator = validator or CertificateValidator()

    def parse(self, path: Path) -> Certificate:
        draft = self._extractor.extract(path)
        if not draft.rows:
            raise CertificateError(["Реестр масок пуст"])

        masks: list[Mask] = []
        problems: list[str] = []
        for row in draft.rows:
            try:
                masks.append(self._compiler.compile(row.mask))
            except ValueError as e:
                problems.append(str(e))
        if problems:
            raise CertificateError(problems)

        problems = self._validator.validate(draft, masks)
        if problems:
            raise CertificateError(problems)
        return Certificate(
            manufacturer=draft.manufacturers[0],
            product_group=draft.product_groups[0],
            masks=tuple(masks),
        )
