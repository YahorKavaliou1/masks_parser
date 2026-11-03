# masks-parser

Сверка артикулов из выгрузки каталога с масками артикулов из сертификата производителя.

## Окружение

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Запуск

```bash
python -m masks_parser --certificate samples/certificate_sample.docx --catalog samples/catalog_sample.xlsx --output data/output/report.xlsx
```

Тесты: `pytest`, линтеры: `ruff check . && ruff format --check .`

### Docker

```bash
docker build -t masks-parser .
docker run --rm --user "$(id -u):$(id -g)" -v "$(pwd)/data:/app/data" masks-parser --certificate data/input/certificate.docx --catalog data/input/catalog.xlsx --output data/output/report.xlsx
```
