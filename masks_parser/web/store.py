import os
import shutil
import tempfile
import time
import uuid
from pathlib import Path


class JobStore:
    """Рабочие папки проверок: загруженные файлы и готовый отчёт.

    Каждая проверка получает папку со случайным id; отчёт отдаётся только по этому id.
    Папки старше `ttl_seconds` удаляются при создании новой проверки.

    Корневая папка общая для всех процессов сервера (gunicorn запускает несколько):
    проверку выполняет один процесс, а отчёт может скачиваться через другой.
    """

    REPORT_NAME = "report.xlsx"
    ROOT_ENV = "MASKS_PARSER_JOBS_DIR"

    @classmethod
    def default_root(cls) -> Path:
        return Path(os.environ.get(cls.ROOT_ENV) or Path(tempfile.gettempdir()) / "masks-parser-jobs")

    def __init__(self, root: Path, ttl_seconds: int = 3600):
        self._root = root
        self._ttl = ttl_seconds
        self._root.mkdir(parents=True, exist_ok=True)

    def create(self) -> tuple[str, Path]:
        self._cleanup()
        job_id = uuid.uuid4().hex
        job_dir = self._root / job_id
        job_dir.mkdir()
        return job_id, job_dir

    def report_path(self, job_id: str) -> Path | None:
        if not self._is_valid_id(job_id):
            return None
        path = self._root / job_id / self.REPORT_NAME
        return path if path.is_file() else None

    def _cleanup(self) -> None:
        expired = time.time() - self._ttl
        for job_dir in self._root.iterdir():
            try:
                is_expired = job_dir.is_dir() and job_dir.stat().st_mtime < expired
            except FileNotFoundError:  # папку уже удалил другой процесс
                continue
            if is_expired:
                shutil.rmtree(job_dir, ignore_errors=True)

    @staticmethod
    def _is_valid_id(job_id: str) -> bool:
        try:
            return uuid.UUID(hex=job_id).hex == job_id
        except ValueError:
            return False
