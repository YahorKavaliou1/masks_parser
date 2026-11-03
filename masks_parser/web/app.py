import tempfile
from dataclasses import dataclass
from pathlib import Path

from flask import Flask, abort, render_template, request, send_file
from werkzeug.datastructures import FileStorage

from masks_parser.certificate import CertificateError
from masks_parser.domain import MatchStatus, show_char
from masks_parser.service import USER_ERRORS, Reconciliation, ReportService
from masks_parser.web.store import JobStore

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "samples"
SAMPLE_FILES = ("certificate_sample.docx", "catalog_sample.xlsx", "catalog_sample.csv")
MAX_UPLOAD_MB = 20
PREVIEW_LIMIT = 200


class UploadError(ValueError):
    """Файл не выбран или у него неподходящее расширение."""


@dataclass(frozen=True)
class Upload:
    """Поле формы: что за файл, какие расширения допустимы."""

    field: str
    title: str
    extensions: tuple[str, ...]

    def save(self, files: dict[str, FileStorage], job_dir: Path) -> tuple[Path, str]:
        file = files.get(self.field)
        if file is None or not file.filename:
            raise UploadError(f"Не выбран файл: {self.title.lower()}")
        suffix = Path(file.filename).suffix.lower()
        if suffix not in self.extensions:
            raise UploadError(
                f"{self.title}: файл «{file.filename}» не подходит, нужен {' или '.join(self.extensions)}"
            )
        # Имя на диске своё: от пользователя берём только расширение, по нему выбирается формат.
        path = job_dir / f"{self.field}{suffix}"
        file.save(path)
        return path, file.filename


CERTIFICATE = Upload("certificate", "Сертификат", (".docx",))
CATALOG = Upload("catalog", "Выгрузка каталога", (".xlsx", ".csv"))


def visible(text: str) -> str:
    """Показывает невидимые символы: краевые пробелы, NBSP, табуляцию, переводы строк."""
    if not text:
        return "(пусто)"
    out = []
    for i, ch in enumerate(text):
        if ch == " ":
            out.append(" " if 0 < i < len(text) - 1 else "␣")
        elif ch.isspace() or not ch.isprintable():
            out.append(f"⟨{show_char(ch)}⟩")
        else:
            out.append(ch)
    return "".join(out)


def create_app(
    service: ReportService | None = None,
    store: JobStore | None = None,
    samples_dir: Path = SAMPLES_DIR,
) -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
    app.jinja_env.filters["visible"] = visible
    service = service or ReportService()
    store = store or JobStore(Path(tempfile.mkdtemp(prefix="masks-parser-")))
    samples = [name for name in SAMPLE_FILES if (samples_dir / name).is_file()]

    def page(status: int = 200, **context):
        context.setdefault("samples", samples)
        context.setdefault("max_upload_mb", MAX_UPLOAD_MB)
        return render_template("index.html", **context), status

    def error_page(title: str, problems: list[str], status: int):
        return page(status, error={"title": title, "problems": problems})

    @app.get("/")
    def index():
        return page()

    @app.post("/check")
    def check():
        job_id, job_dir = store.create()
        try:
            if request.form.get("use_samples") and len(samples) == len(SAMPLE_FILES):
                certificate_path, certificate_name = samples_dir / SAMPLE_FILES[0], SAMPLE_FILES[0]
                catalog_path, catalog_name = samples_dir / SAMPLE_FILES[1], SAMPLE_FILES[1]
            else:
                certificate_path, certificate_name = CERTIFICATE.save(request.files, job_dir)
                catalog_path, catalog_name = CATALOG.save(request.files, job_dir)
            reconciliation = service.check(certificate_path, catalog_path)
            service.write(reconciliation, job_dir / JobStore.REPORT_NAME)
        except UploadError as e:
            return error_page("Проверьте выбранные файлы", [str(e)], 400)
        except CertificateError as e:
            return error_page("Сертификат не прошёл проверку", e.problems, 422)
        except USER_ERRORS as e:
            return error_page("Не удалось обработать файлы", [str(e)], 422)
        return page(result=_result_context(reconciliation, job_id, certificate_name, catalog_name))

    @app.get("/report/<job_id>")
    def report(job_id: str):
        path = store.report_path(job_id)
        if path is None:
            abort(404)
        return send_file(path, as_attachment=True, download_name="masks_report.xlsx")

    @app.get("/samples/<name>")
    def sample(name: str):
        if name not in samples:
            abort(404)
        return send_file(samples_dir / name, as_attachment=True, download_name=name)

    @app.errorhandler(413)
    def too_large(_error):
        return error_page("Файл слишком большой", [f"Максимальный размер загрузки — {MAX_UPLOAD_MB} МБ"], 413)

    return app


def _result_context(reconciliation: Reconciliation, job_id: str, certificate_name: str, catalog_name: str):
    results = reconciliation.results
    return {
        "job_id": job_id,
        "summary": reconciliation.summary,
        "certificate_name": certificate_name,
        "catalog_name": catalog_name,
        "matches": [r for r in results if r.status is MatchStatus.MATCH][:PREVIEW_LIMIT],
        "exceptions": [r for r in results if r.status is MatchStatus.EXCEPTION][:PREVIEW_LIMIT],
        "preview_limit": PREVIEW_LIMIT,
    }
