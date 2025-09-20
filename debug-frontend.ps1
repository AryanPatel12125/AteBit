#!/usr/bin/env pwsh

Write-Host "🔍 Debugging Frontend Container Issues..." -ForegroundColor Cyan

Write-Host "`n📊 Docker Stats:" -ForegroundColor Yellow
try {
    docker stats --no-stream atebit-frontend-1
} catch {
    Write-Host "Container not running" -ForegroundColor Red
}

Write-Host "`n📋 Container Logs (last 50 lines):" -ForegroundColor Yellow
try {
    docker logs --tail 50 atebit-frontend-1
} catch {
    Write-Host "No logs available" -ForegroundColor Red
}

Write-Host "`n🔧 Container Info:" -ForegroundColor Yellow
try {
    docker inspect atebit-frontend-1 --format='{{.State.Status}}: {{.State.ExitCode}}'
} catch {
    Write-Host "Container not found" -ForegroundColor Red
}

Write-Host "`n💾 Memory Usage:" -ForegroundColor Yellow
try {
    docker stats --no-stream --format "table {{.Container}}`t{{.CPUPerc}}`t{{.MemUsage}}`t{{.MemPerc}}" atebit-frontend-1
} catch {
    Write-Host "Stats not available" -ForegroundColor Red
}

Write-Host "`n🌐 Port Status:" -ForegroundColor Yellow
try {
    netstat -an | Select-String ":3000"
} catch {
    Write-Host "Port 3000 not in use" -ForegroundColor Red
}

Write-Host "`n📁 Volume Mounts:" -ForegroundColor Yellow
try {
    docker inspect atebit-frontend-1 --format='{{range .Mounts}}{{.Source}} -> {{.Destination}} ({{.Type}}){{"\n"}}{{end}}'
} catch {
    Write-Host "No mount info available" -ForegroundColor Red
}