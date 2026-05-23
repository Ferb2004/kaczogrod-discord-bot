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
---
### Docker Compose

Plik compose
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
```
---

### Własne budowanie obrazu
Plik compose
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
