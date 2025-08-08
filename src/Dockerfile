FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir flask gunicorn

EXPOSE 8080
CMD ["gunicorn", "-b", ":8080", "app:app"]
