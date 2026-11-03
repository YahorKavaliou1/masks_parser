FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY masks_parser ./masks_parser
COPY samples ./samples

# По умолчанию — веб-интерфейс. Render и другие хостинги передают порт в $PORT.
# Командная строка: docker run … masks-parser python -m masks_parser --certificate … --catalog …
EXPOSE 8000
CMD exec gunicorn "masks_parser.web:create_app()" --bind "0.0.0.0:${PORT:-8000}" --workers 2 --timeout 120 --access-logfile -
