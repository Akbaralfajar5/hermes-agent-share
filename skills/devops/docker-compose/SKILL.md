---
name: docker-compose
description: "Containerize and deploy applications with Docker/Docker Compose — multi-container setup, networking, volumes, PostgreSQL, Redis, and production deployment patterns."
tags: [docker, containers, devops, deployment, orchestration, postgresql, database]
---

# Docker Compose

Containerize applications using Docker and Docker Compose for consistent development and production environments.

## When to Use

- Deploying web applications to VPS
- Setting up multi-service architectures (web + database + cache)
- Creating reproducible development environments
- Isolating application dependencies

## Prerequisites

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

## Common Patterns

### 1. Basic Web App + Database

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: mydb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

### 2. Full Stack with Redis Cache

```yaml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
      - REDIS_URL=redis://cache:6379
    depends_on:
      - db
      - cache

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: mydb
    volumes:
      - postgres_data:/var/lib/postgresql/data

  cache:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 3. Next.js with MongoDB

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "3000:3000"
    environment:
      - MONGODB_URI=mongodb://mongo:27017/mydb
    depends_on:
      - mongo

  mongo:
    image: mongo:7
    volumes:
      - mongo_data:/data/db
    environment:
      - MONGO_INITDB_DATABASE=mydb

volumes:
  mongo_data:
```

## Essential Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
docker-compose logs -f web  # specific service

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# Execute command in container
docker-compose exec web bash
docker-compose exec db psql -U user -d mydb

# View running containers
docker-compose ps

# Remove everything including volumes
docker-compose down -v
```

## Dockerfile Examples

### Node.js / Next.js

```dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy app files
COPY . .

# Build (for Next.js)
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

### Python / FastAPI

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Production Best Practices

1. **Use .dockerignore**
```
node_modules
.git
.env
*.log
```

2. **Environment variables**
```bash
# .env file
DATABASE_URL=postgresql://user:pass@db:5432/mydb
REDIS_URL=redis://cache:6379
```

Load in docker-compose.yml:
```yaml
services:
  web:
    env_file: .env
```

3. **Health checks**
```yaml
services:
  web:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

4. **Resource limits**
```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
```

## Troubleshooting

```bash
# View container logs
docker logs <container_id>

# Inspect container
docker inspect <container_id>

# Enter running container
docker exec -it <container_id> bash

# Check network
docker network ls
docker network inspect <network_name>

# Clean up unused resources
docker system prune -a
```

## Common Issues

**Port already in use:**
```bash
# Find process using port
sudo lsof -i :3000
# Kill process
sudo kill -9 <PID>
```

**Permission denied:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

**Container keeps restarting:**
```bash
# Check logs
docker-compose logs web
# Remove restart policy temporarily
# restart: "no"
```
