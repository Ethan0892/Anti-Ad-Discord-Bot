#!/bin/bash
# Docker Troubleshooting Script for Anti-Ad Bot

echo "==================================="
echo "Docker Container Status"
echo "==================================="
docker-compose ps
echo ""

echo "==================================="
echo "Container Logs - Bot"
echo "==================================="
docker-compose logs --tail=20 anti-ad-bot
echo ""

echo "==================================="
echo "Container Logs - Web Server"
echo "==================================="
docker-compose logs --tail=20 web-server
echo ""

echo "==================================="
echo "Port Status (5000)"
echo "==================================="
netstat -tlnp | grep 5000 || echo "Port 5000 not found"
echo ""

echo "==================================="
echo "Container Network Info"
echo "==================================="
docker network inspect anti-ad-discord-bot_bot-network 2>/dev/null || echo "Network not found"
echo ""

echo "==================================="
echo "Testing Web Server Connectivity"
echo "==================================="
docker-compose exec web-server curl -v http://localhost:5000/api/status || echo "Curl test failed"
echo ""

echo "==================================="
echo "Checking if Python Web Server is Running"
echo "==================================="
docker-compose exec web-server ps aux | grep python || echo "Python process not found"
