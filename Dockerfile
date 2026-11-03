FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY masks_parser ./masks_parser

ENTRYPOINT ["python", "-m", "masks_parser"]
