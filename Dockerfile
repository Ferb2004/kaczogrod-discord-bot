FROM python:3.14.6-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.28 /uv /uvx /bin/

ARG IMAGE_DIGEST=unknown
ENV IMAGE_DIGEST=$IMAGE_DIGEST

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=0

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Kopiowanie kodu źródłowego bota do obrazu kontenera
COPY . .
RUN uv sync --frozen --no-dev

RUN useradd --create-home --shell /usr/sbin/nologin botuser \
    && mkdir -p /app/data /app/logs \
    && chown -R botuser:botuser /app/data /app/logs

USER botuser

# Wykazanie komendy uruchamiania bota podczas startowania kontenera
CMD ["uv", "run", "python", "./app.py"]