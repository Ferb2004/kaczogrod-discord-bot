FROM python:3.13-alpine

ARG IMAGE_DIGEST=unknown
ENV IMAGE_DIGEST=$IMAGE_DIGEST

# Ustawienie zmiennej środowiskowej do uniezależnienia bot od zmian w ścieżkach
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Tworzenie katalogu roboczego w obrazie kontenera
WORKDIR /app

# Instalacja wymaganych zależności z pliku requirements.txt (przed kopiowaniem kodu)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiowanie kodu źródłowego bota do obrazu kontenera
COPY . .

#RUN adduser -D appuser && chown -R appuser:appuser /app
#USER appuser

# Wykazanie komendy uruchamiania bota podczas startowania kontenera
CMD ["python", "./app.py"]
