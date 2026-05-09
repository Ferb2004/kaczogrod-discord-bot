# O projekcie

# Jak zacząć
### Docker Compose
Zalecany sposób
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
### Własne budowanie obrazu docker
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
