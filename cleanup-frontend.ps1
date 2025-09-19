#!/usr/bin/env pwsh

Write-Host "🧹 Cleaning up frontend build artifacts..." -ForegroundColor Cyan

# Stop containers
Write-Host "🛑 Stopping containers..." -ForegroundColor Yellow
docker-compose down

# Remove .next directory if it exists
if (Test-Path "frontend/.next") {
    Write-Host "🗑️ Removing .next directory..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "frontend/.next"
}

# Remove node_modules if it exists (will be recreated by Docker)
if (Test-Path "frontend/node_modules") {
    Write-Host "🗑️ Removing node_modules directory..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "frontend/node_modules"
}

# Remove Docker volumes
Write-Host "🗑️ Removing Docker volumes..." -ForegroundColor Yellow
docker volume rm atebit_frontend_node_modules -f 2>$null
docker volume rm atebit_frontend_next -f 2>$null

# Rebuild and start
Write-Host "🚀 Rebuilding and starting containers..." -ForegroundColor Green
docker-compose up --build

Write-Host "✅ Cleanup complete!" -ForegroundColor Green