# O projekcie

# Jak zacząć
### Docker Compose
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
