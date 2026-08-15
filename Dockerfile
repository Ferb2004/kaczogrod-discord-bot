FROM python:3.14.7-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /uvx /bin/

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=0

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . .
RUN uv sync --frozen --no-dev

FROM gcr.io/distroless/cc-debian12:nonroot AS production

ARG IMAGE_DIGEST=unknown
ENV IMAGE_DIGEST=$IMAGE_DIGEST \
    PATH="/app/.venv/bin:/usr/local/bin:$PATH" \
    PYTHONPATH="/app/.venv/lib/python3.14/site-packages"

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.14 /usr/local/lib/python3.14
COPY --from=builder /usr/local/bin/python3.14 /usr/local/bin/python3.14
COPY --from=builder /app /app

USER nonroot

CMD ["/app/.venv/bin/python3", "./app.py"]