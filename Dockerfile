FROM python:3.14-alpine

COPY --from=ghcr.io/astral-sh/uv:0.11.26 /uv /uvx /bin/

ARG IMAGE_DIGEST=unknown
ENV IMAGE_DIGEST=$IMAGE_DIGEST

WORKDIR /app

# Ustawienie zmiennej środowiskowej do uniezależnienia bot od zmian w ścieżkach
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# Kopiowanie kodu źródłowego bota do obrazu kontenera
COPY . .
RUN uv sync --frozen

# Wykazanie komendy uruchamiania bota podczas startowania kontenera
CMD ["uv", "run", "python", "./app.py"]
