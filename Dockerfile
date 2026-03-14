FROM python:3.12-slim

LABEL maintainer="Soumya Debnath <soumyadebnath1619@gmail.com>"
LABEL description="CyberMentor — AI-powered OWASP security learning platform"
LABEL version="1.0.0"

# Security: run as non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install dependencies first (better layer caching)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Serve frontend as static files from FastAPI
RUN mkdir -p ./static && cp -r frontend/* ./static/

# Set ownership
RUN chown -R appuser:appuser /app

USER appuser

# Environment variables (override at runtime)
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV ANTHROPIC_API_KEY=""
ENV CLAUDE_MODEL="claude-haiku-4-5-20251001"
ENV HOST="0.0.0.0"
ENV PORT="8000"

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
