> [!IMPORTANT]
> Chwilowo development prowadzony jest mocno w kratkę.
---
# O projekcie

# Jak zacząć
## Docker Compose
### Zalecany sposób

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

## Własne budowanie obrazu docker
> [!WARNING]
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
