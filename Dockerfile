FROM python:3.14.7-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /uvx /bin/

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=0

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . .
RUN uv sync --frozen --no-dev

FROM mwader/static-ffmpeg:9.0.1 AS ffmpeg

FROM python:3.14.7-slim-trixie AS production

RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends libopus0 \
    && rm -rf /var/lib/apt/lists/*

ARG IMAGE_DIGEST=unknown
ENV IMAGE_DIGEST=$IMAGE_DIGEST \
    PATH="/app/.venv/bin:/usr/local/bin:$PATH" \
    PYTHONPATH="/app/.venv/lib/python3.14/site-packages"

RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --create-home --shell /usr/sbin/nologin app

WORKDIR /app
COPY --from=builder --chown=app:app /app /app

COPY --from=ffmpeg /ffmpeg /usr/local/bin/ffmpeg
COPY --from=ffmpeg /ffprobe /usr/local/bin/ffprobe

RUN mkdir -p /app/data /app/logs && chown -R app:app /app/data /app/logs

USER app

CMD ["python3", "./app.py"]