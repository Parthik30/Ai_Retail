# ── Base image ──────────────────────────────────────────────────────────────
FROM python:3.11-slim

# ── System dependencies ──────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ────────────────────────────────────────────────────────
WORKDIR /app

# ── Copy requirements first (docker layer caching) ──────────────────────────
COPY requirements.txt .

# ── Install Python dependencies ──────────────────────────────────────────────
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Copy the rest of the project ────────────────────────────────────────────
COPY . .

# ── Streamlit config for headless / server mode ──────────────────────────────
RUN mkdir -p /app/.streamlit
COPY .streamlit/config.toml /app/.streamlit/config.toml

# ── HuggingFace Spaces runs containers as a non-root user (UID 1000) ─────────
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# ── Expose Streamlit port (HF Spaces expects 7860) ───────────────────────────
EXPOSE 7860

# ── Entrypoint ───────────────────────────────────────────────────────────────
CMD ["python", "-m", "streamlit", "run", \
     "backend/streamlit_app/app.py", \
     "--server.port=7860", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]
