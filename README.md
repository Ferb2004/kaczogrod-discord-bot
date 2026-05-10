> [!NOTE]
> Chwilowo development prowadzony jest mocno w kratkę.
# Spis treści
- [O projekcie](#o-projekcie)

- [Jak zacząć](#jak-zaczac)
-  [Docker Compose](#docker-compose)
-  [Własne budowanie obrazu](#wlasne-budowanie-obrazu)
# O projekcie

# Jak zacząć
### Docker Compose

Plik compose
```
version: '3'

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
> [!CAUTION]
> Nie zalecane i robione na własną odpowiedzialność.
Plik compose
```
version: '3'

services:
  kaczogrod-discord-bot:
    build:
      context: https://github.com/Ferb2004/kaczogrod-discord-bot.git
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
- [x] Kanały do liczenia członków online oraz botów na serwerze.
