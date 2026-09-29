FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

RUN pip install --no-cache-dir uv==0.8.*

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY haqqi ./haqqi
RUN uv sync --frozen --no-dev

# Hugging Face Spaces expects port 7860; docker-compose overrides PORT to 8000.
ENV PORT=7860
EXPOSE 7860
RUN useradd --create-home --uid 1000 app
USER app
CMD ["sh", "-c", "uvicorn haqqi.api.main:app --host 0.0.0.0 --port ${PORT}"]
