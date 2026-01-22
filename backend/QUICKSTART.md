# Quick Start Guide

This guide will help you get the Menu Scanner application running in minutes.

## Prerequisites Check

Before starting, ensure you have:
- [ ] Docker installed (version 20.10+)
- [ ] Docker Compose installed (version 2.0+)
- [ ] Git installed
- [ ] 8GB+ RAM available
- [ ] 10GB+ disk space available

## Local Development (5 Minutes)

### Step 1: Clone and Setup (1 minute)

```bash
git clone https://github.com/sontheteacher/Menu-Scanner.git
cd Menu-Scanner
./setup.sh
```

### Step 2: Start Services (2-3 minutes)

```bash
docker-compose up -d
```

Wait for all services to start. You can check status with:
```bash
docker-compose ps
```

### Step 3: Verify Installation (1 minute)

```bash
# Check health
curl http://localhost:8080/api/v1/health

# Expected response:
# {"status":"healthy","timestamp":"...","services":{...}}
```

### Step 4: Try the API

Open your browser and visit:
- **API Documentation**: http://localhost:8080/api-docs
- **Interactive API**: Try uploading a menu image through Swagger UI

Or use curl:
```bash
# Create a test menu image or use one you have
curl -X POST http://localhost:8080/api/v1/menu/upload \
  -F "image=@/path/to/menu.jpg" \
  -F 'options={"extract_prices": true, "extract_descriptions": true}' \
  | jq .
```

## Using Make Commands

The project includes a Makefile for convenience:

```bash
# View all available commands
make help

# Common commands
make start          # Start all services
make stop           # Stop all services
make logs           # View all logs
make logs-api       # View API Gateway logs only
make test-api       # Test API health endpoint
make clean          # Clean up everything
```

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Specific service logs
docker-compose logs api-gateway
docker-compose logs menu-service
docker-compose logs redis
```

### Port Already in Use

If port 8080 is already in use:
1. Edit `docker-compose.yml`
2. Change `"8080:8080"` to `"8081:8080"` under api-gateway ports
3. Restart: `docker-compose down && docker-compose up -d`

### Out of Memory

If services crash due to memory:
1. Close other applications
2. Increase Docker memory limit in Docker Desktop settings
3. Restart services

### Elasticsearch Won't Start

Elasticsearch needs more virtual memory:
```bash
# Linux/macOS
sudo sysctl -w vm.max_map_count=262144

# Add to /etc/sysctl.conf for persistence
vm.max_map_count=262144
```

## What's Running?

After `docker-compose up -d`, you have:

| Service | Port | Purpose |
|---------|------|---------|
| API Gateway | 8080 | REST API & Swagger UI |
| Menu Service | 50051 | gRPC - Menu Processing |
| Image Service | 50052 | gRPC - Image Analysis |
| Redis | 6379 | Cache |
| Memcached | 11211 | Distributed Cache |
| Elasticsearch | 9200 | Search Engine |

## Next Steps

1. **Explore the API**: Visit http://localhost:8080/api-docs
2. **Read the Architecture**: See ARCHITECTURE.md
3. **Try Examples**: Check the README for more API examples
4. **Deploy to Cloud**: Follow the GCP deployment guide in README.md

## Common Tasks

### View Logs in Real-Time
```bash
docker-compose logs -f
```

### Restart a Specific Service
```bash
docker-compose restart api-gateway
```

### Rebuild After Code Changes
```bash
docker-compose build
docker-compose up -d
```

### Stop and Clean Everything
```bash
docker-compose down -v
```

### Export Environment
```bash
docker-compose config
```

## Getting Help

- Check the main README.md for detailed documentation
- View ARCHITECTURE.md to understand the system design
- Open an issue on GitHub for bugs or questions
- Check Docker logs for error messages

## Production Deployment

For production deployment to GCP:
1. Set up GCP account and project
2. Configure Terraform (see terraform/README.md)
3. Run `./deploy.sh`
4. Configure Cloudflare for CDN/WAF

See the main README.md for detailed cloud deployment instructions.
