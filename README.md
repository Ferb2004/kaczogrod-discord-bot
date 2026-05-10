> [!NOTE]
> Chwilowo development prowadzony jest w kratkę.
# Spis treści
- [O projekcie](#o-projekcie)

- [Jak zacząć](#jak-zaczac)
  - [Docker Compose](#docker-compose)
  - [Własne budowanie obrazu](#wlasne-budowanie-obrazu)
- [Funkcje](#funkcje)
# O projekcie

Luźny projekt.

# Jak zacząć
> [!CAUTION]
> Można używać, ale parę rzeczy jeszcze nie działa tak dobrze jak bym chciał.
### Docker Compose

Plik compose
```
services:
  kaczogrod-discord-bot:
    image:
    container_name: discord-bot
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
```

Plik .env
```
DISCORD_TOKEN=
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

Plik .env
```
DISCORD_TOKEN=
```
# Funkcje
- [x] Komenda do rzutu monetą.
- [x] Komenda do przekierowania na githuba.
- [x] Kanały do liczenia członków online oraz botów na serwerze.
