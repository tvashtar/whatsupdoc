# Use Python slim image - most packages have pre-built wheels
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv for faster dependency installation
RUN pip install uv

# Copy dependency files and source structure for package installation
COPY pyproject.toml uv.lock README.md ./
COPY scripts/wsgi.py scripts/wsgi_web.py ./
COPY src/ ./src/

# Install only production dependencies from lock file
RUN uv sync --frozen --no-dev --no-cache

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV MODE=slack

# Cloud Run expects the app to listen on PORT
EXPOSE 8080

# Use production WSGI server for Cloud Run with uv
# Default to Slack bot, but can be overridden with MODE=web for FastAPI
CMD ["sh", "-c", "if [ \"$MODE\" = \"web\" ]; then uv run gunicorn --bind 0.0.0.0:8080 --workers 2 --timeout 60 --worker-class uvicorn.workers.UvicornWorker --preload wsgi_web:application; else uv run gunicorn --bind 0.0.0.0:8080 --workers 2 --timeout 60 --preload wsgi:application; fi"]
