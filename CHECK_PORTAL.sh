#!/bin/bash
# Quick check script to verify admin portal is up to date

echo "=== Checking Admin Portal Status ==="
echo ""
echo "Local commits:"
git log --oneline -5
echo ""
echo "Local index.html size:"
ls -lah templates/index.html
echo ""
echo "Server Configuration mentions in file:"
grep -c "Server Configuration" templates/index.html 2>/dev/null || echo "Not found locally"
echo ""
echo "=== To fix on production server ==="
echo "1. SSH to production"
echo "2. cd /opt/Anti-Ad-Discord-Bot"
echo "3. git pull origin main"
echo "4. docker-compose down"
echo "5. docker-compose up -d --build"
echo "6. Clear browser cache and refresh: Ctrl+Shift+R"
echo ""
echo "If still not showing:"
echo "7. docker exec anti-ad-web ls -la /app/templates/index.html"
echo "8. docker exec anti-ad-web grep 'Server Configuration' /app/templates/index.html"
