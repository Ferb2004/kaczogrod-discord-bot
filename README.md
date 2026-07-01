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
</p>

# Spis treści
- [O projekcie](#o-projekcie)

- [Jak zacząć](#jak-zaczac)
  - [Docker Compose](#docker-compose)
  - [Plik .env](#plik-.env)
  - [Własne budowanie obrazu](#wlasne-budowanie-obrazu)
- [Funkcje](#funkcje)
# O projekcie

Luźny projekt.


# Jak zacząć

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
      - ./data:/app/data
      - ./logs:/app/logs
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
```
---

### Własne budowanie obrazu
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
      - ./data:/app/data
      - ./logs:/app/logs
```
# Funkcje
- [x] Komenda do rzutu monetą.
- [x] Komenda do przekierowania na githuba.
- [x] Kanały do liczenia członków online oraz botów na serwerze.
- [x] Pokazywanie liczby graczy na serwerze minecraft w statusie.
- [x] Komenda do wyświetlania informacji o serwerach minecraft.
