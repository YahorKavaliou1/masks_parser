import io
import os
import time

import pytest
from openpyxl import load_workbook

from masks_parser.web.app import create_app, visible
from masks_parser.web.store import JobStore
from scripts.make_sample_certificate import build_certificate
from tests import hilex


@pytest.fixture
def store(tmp_path) -> JobStore:
    return JobStore(tmp_path / "jobs")


@pytest.fixture
def client(store):
    return create_app(store=store).test_client()


def _upload(name: str, data: bytes | None = None):
    return (io.BytesIO(data if data is not None else (hilex.SAMPLES / name).read_bytes()), name)


def _check(client, certificate=None, catalog=None):
    files = {}
    if certificate:
        files["certificate"] = certificate
    if catalog:
        files["catalog"] = catalog
    return client.post("/check", data=files, content_type="multipart/form-data")


def test_index_explains_steps_and_offers_samples(client):
    page = client.get("/").get_data(as_text=True)
    assert "Масочный сертификат" in page and "Выгрузка каталога" in page
    assert "Что именно проверяется" in page
    assert "Проверить на примерах" in page


def test_index_hides_samples_when_absent(store, tmp_path):
    page = (
        create_app(store=store, samples_dir=tmp_path / "none").test_client().get("/").get_data(as_text=True)
    )
    assert "Проверить на примерах" not in page


@pytest.mark.parametrize("catalog", ["catalog_sample.xlsx", "catalog_sample.csv"])
def test_upload_shows_result_and_report(client, catalog):
    response = _check(client, _upload("certificate_sample.docx"), _upload(catalog))
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Проверка завершена" in page
    assert f"{hilex.MANUFACTURER} · {hilex.GROUP}" in page
    for label, value in (("Строк в выгрузке", 214), ("Соответствует", 123), ("Исключений", 91)):
        assert f"<dt>{label}</dt><dd>{value}</dd>" in page
    assert "Префикс отсутствует в перечне масок" in page

    report_url = page.split('href="/report/')[1].split('"')[0]
    report = client.get(f"/report/{report_url}")
    assert report.status_code == 200
    assert "masks_report.xlsx" in report.headers["Content-Disposition"]
    workbook = load_workbook(io.BytesIO(report.data))
    assert workbook.sheetnames == ["Соответствует", "Исключения", "Сводка"]


def test_check_on_samples(client):
    page = client.post("/check", data={"use_samples": "1"}).get_data(as_text=True)
    assert "Проверка завершена" in page
    assert "certificate_sample.docx" in page and "catalog_sample.xlsx" in page


def test_invisible_chars_are_shown_and_html_is_escaped(client, tmp_path):
    catalog = (
        "Производитель;Товарная группа;Артикул\n"
        f"{hilex.MANUFACTURER};{hilex.GROUP};<script>alert(1)</script>\n"
        f"{hilex.MANUFACTURER};{hilex.GROUP};4VB 1234\n"
    ).encode()
    page = _check(client, _upload("certificate_sample.docx"), _upload("c.csv", catalog)).get_data(
        as_text=True
    )
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page
    assert "4VB⟨U+00A0⟩1234" in page  # исходный артикул показан с видимым NBSP


@pytest.mark.parametrize(
    ("files", "message"),
    [
        ({"catalog": True}, "Не выбран файл: сертификат"),
        ({"certificate": True}, "Не выбран файл: выгрузка каталога"),
        ({"certificate": "c.pdf", "catalog": True}, "Сертификат: файл «c.pdf» не подходит, нужен .docx"),
        ({"certificate": True, "catalog": "c.xls"}, "файл «c.xls» не подходит, нужен .xlsx или .csv"),
    ],
)
def test_upload_errors(client, files, message):
    certificate = files.get("certificate")
    catalog = files.get("catalog")
    response = _check(
        client,
        _upload("certificate_sample.docx")
        if certificate is True
        else (certificate and _upload(certificate, b"x")),
        _upload("catalog_sample.xlsx") if catalog is True else (catalog and _upload(catalog, b"x")),
    )
    page = response.get_data(as_text=True)
    assert response.status_code == 400
    assert "Проверьте выбранные файлы" in page
    assert message in page


def test_inconsistent_certificate_lists_all_problems(client, tmp_path):
    certificate = build_certificate(tmp_path / "c.docx", declared=39, listed=hilex.MASKS[:-1])
    response = _check(
        client, (io.BytesIO(certificate.read_bytes()), "c.docx"), _upload("catalog_sample.xlsx")
    )
    page = response.get_data(as_text=True)
    assert response.status_code == 422
    assert "Сертификат не прошёл проверку" in page
    assert "В тексте заявлено 39 масок, в реестре 38" in page
    assert "нет масок из реестра: 9BB****" in page


def test_broken_catalog(client):
    response = _check(client, _upload("certificate_sample.docx"), _upload("c.xlsx", b"not an xlsx"))
    assert response.status_code == 422
    assert "Файл не является книгой Excel .xlsx" in response.get_data(as_text=True)


def test_too_large_upload(store):
    app = create_app(store=store)
    app.config["MAX_CONTENT_LENGTH"] = 10
    response = _check(app.test_client(), _upload("certificate_sample.docx"), _upload("catalog_sample.xlsx"))
    assert response.status_code == 413
    assert "Файл слишком большой" in response.get_data(as_text=True)


@pytest.mark.parametrize("job_id", ["missing", "../../etc/passwd", "0" * 32])
def test_unknown_report_is_404(client, job_id):
    assert client.get(f"/report/{job_id}").status_code == 404


def test_samples_download_is_whitelisted(client):
    assert client.get("/samples/catalog_sample.csv").status_code == 200
    assert client.get("/samples/catalog_expected.csv").status_code == 404
    assert client.get("/samples/..%2FREADME.md").status_code == 404


def test_old_jobs_are_removed(tmp_path):
    store = JobStore(tmp_path / "jobs", ttl_seconds=60)
    old_id, old_dir = store.create()
    (old_dir / JobStore.REPORT_NAME).write_bytes(b"x")
    past = time.time() - 120
    os.utime(old_dir, (past, past))
    assert store.report_path(old_id) is not None
    store.create()
    assert store.report_path(old_id) is None


@pytest.mark.parametrize(
    ("text", "shown"),
    [
        ("", "(пусто)"),
        ("4VB0000", "4VB0000"),
        (" 4VB 0000 ", "␣4VB 0000␣"),
        ("4VB\t00\n", "4VB⟨U+0009⟩00⟨U+000A⟩"),
        ("4VB​0", "4VB⟨U+200B⟩0"),
    ],
)
def test_visible(text, shown):
    assert visible(text) == shown


def test_report_is_available_from_another_worker(tmp_path):
    # gunicorn запускает несколько процессов: проверка в одном, скачивание — в другом.
    root = tmp_path / "jobs"
    first = create_app(store=JobStore(root)).test_client()
    second = create_app(store=JobStore(root)).test_client()
    page = first.post("/check", data={"use_samples": "1"}).get_data(as_text=True)
    job_id = page.split('href="/report/')[1].split('"')[0]
    assert second.get(f"/report/{job_id}").status_code == 200


def test_default_root_is_shared_and_configurable(monkeypatch, tmp_path):
    monkeypatch.delenv(JobStore.ROOT_ENV, raising=False)
    assert JobStore.default_root() == JobStore.default_root()
    assert JobStore.default_root().name == "masks-parser-jobs"
    monkeypatch.setenv(JobStore.ROOT_ENV, str(tmp_path / "custom"))
    assert JobStore.default_root() == tmp_path / "custom"
