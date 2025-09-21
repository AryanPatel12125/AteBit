#!/bin/bash

echo "🔍 Debugging Frontend Container Issues..."

echo "📊 Docker Stats:"
docker stats --no-stream atebit-frontend-1 2>/dev/null || echo "Container not running"

echo ""
echo "📋 Container Logs (last 50 lines):"
docker logs --tail 50 atebit-frontend-1 2>/dev/null || echo "No logs available"

echo ""
echo "🔧 Container Info:"
docker inspect atebit-frontend-1 --format='{{.State.Status}}: {{.State.ExitCode}}' 2>/dev/null || echo "Container not found"

echo ""
echo "💾 Memory Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" atebit-frontend-1 2>/dev/null || echo "Stats not available"

echo ""
echo "🌐 Port Status:"
netstat -tulpn | grep :3000 || echo "Port 3000 not in use"

echo ""
echo "📁 Volume Mounts:"
docker inspect atebit-frontend-1 --format='{{range .Mounts}}{{.Source}} -> {{.Destination}} ({{.Type}}){{"\n"}}{{end}}' 2>/dev/null || echo "No mount info available"