# Docker Development Setup

This project is configured for optimal development experience with Docker, including hot reloading and file watching.

## Quick Start

```bash
# Start development environment with watch mode
docker-compose up --build

# Or use the new Docker Compose watch feature (Docker Compose v2.22+)
docker-compose watch
```

## Development Features

### 🔥 Hot Reloading Enabled

- **Frontend (Next.js)**: Automatic browser refresh on file changes
- **Backend (Django)**: Automatic server restart on Python file changes
- **File Watching**: Real-time sync between host and container

### 📁 Volume Mounts

- Source code is mounted for live editing
- Node modules and build artifacts are preserved in named volumes
- Static files are handled separately

### 🚀 Development Optimizations

- Development dependencies included
- Debug mode enabled
- Detailed logging
- Fast rebuild on dependency changes

## Docker Compose Watch Mode

The configuration includes Docker Compose's new `watch` feature for optimal development:

```yaml
develop:
  watch:
    - action: sync          # Live sync file changes
    - action: rebuild       # Rebuild on dependency changes
```

### Watch Actions

- **sync**: Real-time file synchronization (code changes)
- **rebuild**: Container rebuild (dependency changes)

## Commands

### Development
```bash
# Start with watch mode (recommended)
docker-compose watch

# Traditional development start
docker-compose up --build

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart frontend
docker-compose restart backend
```

### Production
```bash
# Production build
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

### Debugging
```bash
# Shell into containers
docker-compose exec backend bash
docker-compose exec frontend sh

# View container status
docker-compose ps

# Check resource usage
docker stats
```

## File Structure

```
├── docker-compose.yml              # Main development config
├── docker-compose.override.yml     # Development overrides (auto-loaded)
├── docker-compose.prod.yml         # Production overrides
├── backend/
│   ├── Dockerfile                  # Production backend image
│   ├── Dockerfile.dev              # Development backend image
│   └── .dockerignore              # Backend build exclusions
└── frontend/
    ├── Dockerfile                  # Production frontend image
    ├── Dockerfile.dev              # Development frontend image
    └── .dockerignore              # Frontend build exclusions
```

## Environment Variables

### Backend
- `DEBUG=True` - Django debug mode
- `DJANGO_LOG_LEVEL=DEBUG` - Detailed logging
- `PYTHONUNBUFFERED=1` - Real-time Python output

### Frontend
- `NODE_ENV=development` - Next.js development mode
- `WATCHPACK_POLLING=true` - File watching in containers
- `CHOKIDAR_USEPOLLING=true` - Cross-platform file watching

## Troubleshooting

### File Changes Not Detected
```bash
# Ensure polling is enabled for cross-platform compatibility
# Already configured in docker-compose.yml
```

### Slow Performance
```bash
# Use Docker Desktop with WSL2 backend on Windows
# Ensure adequate resources allocated to Docker
```

### Port Conflicts
```bash
# Change ports in docker-compose.yml if needed
ports:
  - "3001:3000"  # Frontend
  - "8001:8000"  # Backend
```

### Container Rebuild
```bash
# Force rebuild after dependency changes
docker-compose up --build

# Clean rebuild
docker-compose down
docker-compose up --build --force-recreate
```

## Performance Tips

1. **Use Docker Desktop with WSL2** (Windows)
2. **Allocate sufficient resources** (4GB+ RAM recommended)
3. **Use .dockerignore** to exclude unnecessary files
4. **Named volumes** for node_modules and build artifacts
5. **File watching optimizations** already configured

## Next Steps

- The development environment is ready for coding
- File changes will automatically trigger rebuilds/reloads
- Use `docker-compose logs -f` to monitor both services
- Access frontend at http://localhost:3000
- Access backend at http://localhost:8000