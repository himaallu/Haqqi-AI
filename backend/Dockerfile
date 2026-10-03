# Build from the repo root (see render.yaml and docker-compose.yml) so the law data can be copied in.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH" \
    LAW_DATA_DIR=/app/data/law

RUN pip install --no-cache-dir uv==0.8.*

WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY backend/haqqi ./haqqi
RUN uv sync --frozen --no-dev

# Law text and the Law Pack: retrieval and citation checks read them at runtime.
COPY data/law/*.json ./data/law/
RUN python -c "from haqqi.rag.lawdata import load_chunks, load_law_pack; load_law_pack(); assert load_chunks()"

# Hosts such as Render set PORT; 8000 is the local default.
ENV PORT=8000
EXPOSE 8000
RUN useradd --create-home --uid 1000 app
USER app
CMD ["sh", "-c", "uvicorn haqqi.api.main:app --host 0.0.0.0 --port ${PORT}"]
