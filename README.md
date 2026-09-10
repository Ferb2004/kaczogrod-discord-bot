<p align="center">
<img src="./media/baner.jpeg" alt="Baner" width="400">
</p>

<p align="center">
  <a href="https://github.com/Ferb2004/kaczogrod-discord-bot/releases"><img src="https://img.shields.io/github/v/release/Ferb2004/kaczogrod-discord-bot?style=for-the-badge&color=2496ED&label=release" alt="Latest release"></a>
  <a href="https://github.com/Ferb2004/kaczogrod-discord-bot/pkgs/container/kaczogrod-discord-bot"><img src="https://img.shields.io/badge/docker-available-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker image"></a>
</p>

<p align="center">
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/badge/ruff-%23D7FF64?style=for-the-badge&logo=ruff&logoColor=black" alt="Ruff"></a>
  <a href="https://github.com/astral-sh/uv"><img alt="uv" src="https://img.shields.io/badge/uv-%23DE5FE9.svg?style=for-the-badge&logo=uv&logoColor=white"></a>
  <a href="https://github.com/microsoft/pyright"><img src="https://img.shields.io/badge/pyright-checked-%231674b1?style=for-the-badge" alt="Pyright"></a>
  <a href="https://madebyhuman.iamjarl.com"><img src="https://madebyhuman.iamjarl.com/badges/co-created-white.svg" height="28"></a>
</p>

# Spis treści
- [O projekcie](#o-projekcie)
  - [Użycie AI](#użycie-ai)

- [Instalacja](#instalacja)
  - [Docker Compose](#docker-compose)
  - [Plik .env](#plik-env)
  - [Budowanie własnego obrazu](#budowanie-własnego-obrazu)
- [Funkcje](#funkcje)
- [Planowane funkcje](#planowane-funkcje)
- [Checki](#checki)
# O projekcie

Self hostowalny w dockerze bot discord, napisany w pythonie. Przeznaczony do użytku na małej ilości serwerów, głównie dla znajomych.

# Użycie AI
AI było używane głównie jako pomoc w znalezieniu i wytłumaczeniu, jakie podejście do danego problemu jest najlepsze. Zostało użyte z braku podobnych projektów z ADR (lub innej dokumentacji, która dobrze opisywałaby działanie bota). AI było też używane do pomocy w szukaniu zależności, które odpowiadały potrzebom projektu.

# Instalacja

### Docker Compose
```
services:
  kaczogrod-discord-bot:
    image: ghcr.io/ferb2004/kaczogrod-discord-bot:latest
    container_name: discord-bot
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - bot-data:/app/data
      - bot-logs:/app/logs
volumes:
  bot-data: null
  bot-logs: null
```
---

### Plik .env
```
DISCORD_TOKEN=

#---Opcjonalne---
#Ip serwera minecraft, którego liczba graczy ma być pokazywana.
IP_SERWERA=
#Port serwera minecraft. Jeśli nie będzie podany, bot będzie sprawdzał na porcie 25565.
PORT_SERWERA=
#Potrzebne, jeśli bot ma odtwarzać muzykę ze spotify.
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
#Więcej informacji w logach.
LOG_LEVEL=DEBUG
```
---

### Budowanie własnego obrazu
```
services:
  kaczogrod-discord-bot:
    build:
      context: https://github.com/Ferb2004/kaczogrod-discord-bot.git#main
    container_name: discord-bot
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - bot-data:/app/data
      - bot-logs:/app/logs
volumes:
  bot-data: null
  bot-logs: null
```
# Funkcje
-  Komenda do rzutu monetą.
-  Komenda do przekierowania na githuba.
-  Kanały do liczenia członków online oraz botów na serwerze.
-  Pokazywanie liczby graczy na serwerze minecraft w statusie.
-  Komenda do wyświetlania informacji o serwerach minecraft.
-  Wysyłanie feedów RSS/Atom.
-  Nadawanie roli użytkownikom przy dołączeniu na serwer.
-  Role, które użytkownicy mogą sami sobie wybrać.
-  Puszczanie muzyki.

# Planowane funkcje
- Dodanie embedów oraz przycisków do coga z muzyką.
- Wysyłanie cen z GGDEALS.
- Tymczasowe kanały.


# Checki
Checki, które projekt przechodzi.
- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run pyright .`
